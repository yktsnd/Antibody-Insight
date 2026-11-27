"""Inspect deposited coordinates and compare explicitly matched protein chains."""
import hashlib
import io
import json
import warnings

from Bio.Data.PDBData import protein_letters_3to1
import numpy as np
from Bio.PDB import MMCIFParser, PDBIO, PDBParser, Superimposer, is_aa
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.PDB.PDBExceptions import PDBConstructionWarning

from .imports import LIMIT
from .project import connection, now, uid


def cif_mappings(text, sequence, model):
    """Join polymer positions to observed author keys. Unobserved positions stay empty."""
    data = MMCIF2Dict(io.StringIO(text))
    def rows(category, fields):
        columns = [data.get(category + "." + field, []) for field in fields.split()]
        return zip(*columns) if len({len(col) for col in columns}) == 1 else ()

    polymers = {}
    invalid_entities = set()
    for entity, number, monomer in rows("_entity_poly_seq", "entity_id num mon_id"):
        positions = polymers.setdefault(entity, {})
        if not number.isdigit() or int(number) in positions or monomer not in protein_letters_3to1:
            invalid_entities.add(entity)
            continue
        positions[int(number)] = monomer
    matches = {entity for entity, positions in polymers.items() if entity not in invalid_entities
               and len(positions) == len(sequence)
               and all(protein_letters_3to1.get(positions.get(i)) == aa for i,aa in enumerate(sequence,1))}
    if not matches:
        return {}
    owners = {}
    for label, entity in rows("_struct_asym", "id entity_id"):
        if label in owners:
            return {}
        owners[label] = entity
    fields = "group_PDB label_asym_id label_entity_id label_seq_id label_comp_id auth_asym_id auth_seq_id pdbx_PDB_ins_code"
    if any("_atom_site."+field not in data for field in fields.split()):
        return {}
    observed, label_chains, invalid, auth_chains = {}, {}, set(), {}
    for group, label, entity, number, monomer, author, resi, insertion in rows("_atom_site", fields):
        if group != "ATOM" and number in (".","?"):
            continue
        auth_chains.setdefault(author,set()).add(label)
        if owners.get(label) not in matches:
            continue
        label_chains.setdefault(label,set()).add(author)
        declared = polymers[owners[label]]
        if (entity != owners[label] or group != "ATOM" or not number.isdigit() or declared.get(int(number)) != monomer
                or not resi.lstrip("-").isdigit()):
            invalid.add(label)
            continue
        key = (int(resi), "" if insertion in ("?",".") else insertion)
        positions = observed.setdefault(label,{})
        if positions.setdefault(int(number),key) != key:
            invalid.add(label)
    mappings = {}
    for label, positions in observed.items():
        if label in invalid or len(label_chains[label]) != 1 or len(set(positions.values())) != len(positions):
            continue
        author = next(iter(label_chains[label]))
        if len(auth_chains[author]) != 1 or author not in model:
            continue
        chain = model[author]
        values = [None]*len(sequence)
        for n,(number,insertion) in positions.items():
            residue = chain.child_dict.get((" ",number,insertion or " "))
            if residue is None or residue.is_disordered()==2 or residue.resname != polymers[owners[label]][n]:
                break
            if any(atom.occupancy is not None and atom.occupancy > 0 for atom in residue.get_unpacked_list()):
                values[n-1] = [number,insertion]
        else:
            if any(values):
                mappings[author] = values
    return mappings


def pdb_mappings(text, sequence, model):
    declared = {}
    for line in text.splitlines():
        if line.startswith("SEQRES"):
            declared.setdefault(line[11:12],[]).extend(line[19:].split())
    mappings = {}
    for chain in model:
        if chain.id in declared and "".join(protein_letters_3to1.get(m,"?") for m in declared[chain.id]) != sequence:
            continue
        residues = [r for r in chain if r.id[0] == " " or is_aa(r)]
        letters = "".join(protein_letters_3to1.get(r.resname,"?") for r in residues)
        if letters == sequence and all(r.id[0]==" " and r.is_disordered()!=2 for r in residues):
            positions = [[r.id[1],r.id[2].strip()]
                         if any(a.occupancy is not None and a.occupancy>0 for a in r.get_unpacked_list())
                         else None for r in residues]
            if any(positions):
                mappings[chain.id] = positions
    return mappings


def parse_coordinates(raw, filename, component):
    if len(raw) > LIMIT:
        raise ValueError("Coordinate file exceeds 24 MiB.")
    is_cif = filename.lower().endswith((".cif",".mmcif"))
    text = raw.decode("utf-8-sig")
    parser = MMCIFParser() if is_cif else PDBParser(PERMISSIVE=False)
    with warnings.catch_warnings():
        warnings.filterwarnings("error", category=PDBConstructionWarning, message=".*(redefined|duplicate|discontinuous).*")
        if is_cif:
            # Depositions commonly append waters after all polymer chains.
            warnings.filterwarnings("ignore", category=PDBConstructionWarning, message="WARNING: Chain .* is discontinuous at line")
        model_set = parser.get_structure("input", io.StringIO(text))
    models = list(model_set)
    if len(models) != 1:
        raise ValueError("Choose a single-model coordinate file.")
    model = models[0]
    mappings = {}
    if component["kind"] == "AA":
        mappings = (cif_mappings if is_cif else pdb_mappings)(text,component["seq"],model)
    output = io.StringIO()
    writer = PDBIO()
    writer.set_structure(model)
    writer.save(output)
    return dict(raw=raw, sha=hashlib.sha256(raw).hexdigest(), filename=filename, display=output.getvalue(),
                component=component["id"], mappings=mappings, chains=[c.id for c in model])


def preview(path, component):
    if path.stat().st_size > LIMIT:
        raise ValueError("Coordinate file exceeds 24 MiB.")
    return parse_coordinates(path.read_bytes(),path.name,component)


def save(path, packet, chain, origin):
    if chain is not None and chain not in packet["mappings"]:
        raise ValueError("The selected chain lacks an exact sequence match.")
    if origin not in {"Unknown", "Experimental", "Predicted", "Reference"}:
        raise ValueError("Specify the coordinate origin.")
    with connection(path) as db:
        db.execute("INSERT OR IGNORE INTO source VALUES(?,?)",(packet["sha"],packet["raw"]))
        db.execute("INSERT INTO structure VALUES(?,?,?,?,?,?,?,?,?)",
                   (uid(),packet["component"],packet["filename"],packet["sha"],now(),chain or "",origin,
                    packet["display"],json.dumps({"positions":packet["mappings"].get(chain,[]),"version":2})))


def alpha_carbons(data):
    model = PDBParser(PERMISSIVE=False).get_structure("coordinates",io.StringIO(data["display_pdb"]))[0]
    chain = model[data["chain"]]
    atoms = {}
    for index,key in enumerate(data["mapping"],1):
        if key is None:
            continue
        residue = chain.child_dict.get((" ",key[0],key[1] or " "))
        atom = residue["CA"] if residue is not None and "CA" in residue else None
        if atom is not None and not atom.is_disordered() and atom.occupancy and atom.occupancy>0:
            if np.isfinite(atom.coord).all():
                atoms[index] = atom
    return atoms


def superpose(fixed,moving,columns):
    """Return a proper rigid transform for the observed, unambiguous Cα pairs."""
    if not fixed["mapping"] or not moving["mapping"]:
        raise ValueError("Both structures need a mapped protein chain.")
    fixed_atoms,moving_atoms = alpha_carbons(fixed),alpha_carbons(moving)
    pairs = [[a,b] for a,b in columns if a in fixed_atoms and b in moving_atoms]
    if len(pairs)<3:
        raise ValueError("Superposition needs at least three shared, unambiguous Cα atoms.")
    atom_sets = ([fixed_atoms[a] for a,_ in pairs],[moving_atoms[b] for _,b in pairs])
    for atoms in atom_sets:
        positions = np.array([a.coord for a in atoms],dtype=float)
        if np.linalg.matrix_rank(positions-positions.mean(axis=0),tol=1e-6)<2:
            raise ValueError("The matched Cα atoms lie on a line.")
    fit = Superimposer()
    fit.set_atoms(*atom_sets)
    rotation,translation = fit.rotran
    return dict(rotation=rotation.tolist(),translation=translation.tolist(),rmsd=float(fit.rms),
                pairs=pairs,correspondence=columns)
