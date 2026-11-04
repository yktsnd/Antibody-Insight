"""Local coordinate observations and explicit correspondence. F08 / J03,J04,J08.

No sequence alignment, structural superposition, confidence inference or prediction.
"""

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import hashlib
import math
import re

from .domain import ValidationError, fields, identifier, nullable_text, number, require, source, text

RESIDUE_FIELDS = {"model", "auth_chain", "label_asym", "segment", "auth_number", "label_number", "insertion_code", "residue_name"}
CHAIN_FIELDS = {"model", "auth_chain", "label_asym", "segment"}
STANDARD_AA = dict(zip("ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL".split(), "ARNDCQEGHILKMFPSTWYV"))
MAX_ATOMS = 100000
MAX_TEXT = 24 * 1024 * 1024


def residue_key(residue):
    return tuple(residue[key] for key in sorted(RESIDUE_FIELDS))


def chain_key(chain):
    return tuple(chain[key] for key in sorted(CHAIN_FIELDS))


def _float(token, optional=False):
    if token is None or token.strip() in ("", ".", "?"):
        require(optional, "Coordinate field is missing")
        return None
    try:
        value = float(token)
        require(math.isfinite(value) and (value != 0 or Decimal(token) == 0), "Coordinate number overflows or underflows")
        number(value, "coordinate/source numeric field")
        return value
    except (ValueError, OverflowError, InvalidOperation) as exc:
        raise ValidationError("Malformed coordinate/source numeric field") from exc


def _int(token, optional=False):
    if token is None or token.strip() in ("", ".", "?"):
        require(optional, "Source numeric identifier is missing")
        return None
    require(re.fullmatch(r"[+-]?[0-9]+", token.strip()) is not None, "Unsupported or malformed numeric identifier (hybrid-36 is not supported)")
    value = int(token)
    require(abs(value) <= 2**53 - 1, "Source identifier exceeds interoperable integer range")
    return value


def _cif_id(value):
    return None if value is None or value in (".", "?") else value


def _cif_code(value):
    return None if value is None or value == "?" else "" if value == "." else value


def _pdb_atoms(content, gemmi):
    try:
        gemmi.read_pdb_string(content)  # syntax read only; no entity/label/conformer assignment
    except (RuntimeError, ValueError) as exc:
        raise ValidationError("Invalid PDB syntax") from exc
    model, explicit, opened, seen_models, any_atoms = 1, False, False, set(), False
    atoms, part, residue_parts = [], 0, {}
    for line in content.splitlines():
        record = line[:6].strip()
        if record == "MODEL":
            require(not opened and not (any_atoms and not explicit), "Mixed or nested PDB model records")
            model = _int(line[10:14]); require(model > 0 and model not in seen_models, "Invalid/duplicate model identifier")
            seen_models.add(model); opened = explicit = True
        elif record == "ENDMDL":
            require(opened, "Unmatched PDB ENDMDL")
            opened = False
        elif record == "TER":
            part += 1
        elif record in ("ATOM", "HETATM"):
            require(not explicit or opened, "Atoms outside an explicit PDB model")
            require(len(line) >= 54, "Truncated PDB atom record")
            serial = _int(line[6:11]); require(serial > 0, "Invalid PDB atom identifier")
            segment = line[72:76].strip() if len(line) >= 76 else None
            source_locus = (model, line[21:22], segment, _int(line[22:26]), line[26:27].strip())
            require(source_locus not in residue_parts or residue_parts[source_locus] == part,
                    "Ambiguous PDB residue locus reused across TER; supply distinct source segments or mmCIF residue identifiers")
            residue_parts[source_locus] = part
            atoms.append({"model": model, "auth_chain": line[21:22], "label_asym": None, "segment": segment,
                          "auth_number": _int(line[22:26]), "label_number": None, "insertion_code": line[26:27].strip(),
                          "residue_name": line[17:20].strip(), "atom_name": line[12:16].strip(), "altloc": line[16:17].strip(),
                          "source_atom_id": str(serial), "x": _float(line[30:38]), "y": _float(line[38:46]), "z": _float(line[46:54]),
                          "occupancy": _float(line[54:60], True), "b_value": _float(line[60:66], True),
                          "element": line[76:78].strip(), "hetero": record == "HETATM"})
            any_atoms = True
            require(len(atoms) <= MAX_ATOMS, "Structure exceeds 100,000 atoms")
    require(not opened, "Unclosed PDB model")
    return atoms


def _cif_atoms(content, gemmi):
    try:
        document = gemmi.cif.read_string(content)
        require(len(document) == 1, "One coordinate data block per mmCIF input is supported")
        block = document[0]
        table = block.find_mmcif_category("_atom_site.")
        require(bool(table) and len(table) <= MAX_ATOMS, "Missing atom_site or structure exceeds 100,000 atoms")
        tags = [tag.lower().split(".", 1)[1] for tag in table.tags]
        require(len(set(tags)) == len(tags), "Duplicate atom_site field")
        atoms = []
        for row in table:
            data = dict(zip(tags, row))
            def get(name): return data.get(name)
            def cid(name):
                value = get(name)
                return None if value is None or value in (".", "?") else gemmi.cif.as_string(value)
            def code(name):
                value = get(name)
                return None if value is None or value == "?" else "" if value == "." else gemmi.cif.as_string(value)
            def numeric(name):
                value = get(name)
                if value is None or value in (".", "?"): return value
                decoded = gemmi.cif.as_string(value)
                require(decoded not in (".", "?"), "Quoted CIF missing-marker literals are not numeric fields")
                return decoded
            group = cid("group_pdb")
            require(group in ("ATOM", "HETATM"), "Unsupported atom_site record type")
            model = _int(numeric("pdbx_pdb_model_num"), True)
            require(model is None or model > 0, "Invalid mmCIF model identifier")
            atoms.append({"model": model, "auth_chain": cid("auth_asym_id"), "label_asym": cid("label_asym_id"),
                          "segment": code("pdbx_pdb_segment_id"), "auth_number": _int(numeric("auth_seq_id"), True),
                          "label_number": _int(numeric("label_seq_id"), True), "insertion_code": code("pdbx_pdb_ins_code"),
                          "residue_name": cid("label_comp_id"), "auth_residue_name": cid("auth_comp_id"),
                          "atom_name": cid("label_atom_id"), "altloc": code("label_alt_id"),
                          "source_atom_id": cid("id"), "x": _float(numeric("cartn_x")), "y": _float(numeric("cartn_y")), "z": _float(numeric("cartn_z")),
                          "occupancy": _float(numeric("occupancy"), True), "b_value": _float(numeric("b_iso_or_equiv"), True),
                          "element": cid("type_symbol") or "", "hetero": group == "HETATM"})
        return atoms
    except ValidationError:
        raise
    except (RuntimeError, ValueError, IndexError) as exc:
        raise ValidationError("Invalid mmCIF syntax or atom_site fields") from exc


@lru_cache(maxsize=8)
def parse_structure(content, file_format):
    require(isinstance(content, str) and 0 < len(content.encode("utf-8")) <= MAX_TEXT, "Coordinate text must contain 1–24MiB")
    require(file_format in ("pdb", "mmcif"), "Unsupported coordinate format")
    try:
        import gemmi
    except ImportError as exc:
        raise ValidationError("Local structural parser unavailable; install requirements.txt in the application environment") from exc
    require(gemmi.__version__ == "0.7.5", "Unsupported parser version; use pinned Gemmi0.7.5")
    atoms = _pdb_atoms(content, gemmi) if file_format == "pdb" else _cif_atoms(content, gemmi)
    require(bool(atoms), "No coordinate atoms found")
    residues, atom_ids, atom_sites, chains = {}, set(), set(), {}
    for atom in atoms:
        for field in ("residue_name", "atom_name", "source_atom_id"):
            text(atom[field], field, 100)
        require(atom["auth_chain"] is not None or atom["label_asym"] is not None, "Source chain identifier unavailable")
        require(atom["auth_number"] is not None or atom["label_number"] is not None, "Source residue identifier unavailable")
        for key in ("auth_chain", "label_asym", "segment", "insertion_code"):
            require(atom[key] is None or isinstance(atom[key], str) and len(atom[key]) <= 100, "Invalid source residue key")
        require(atom["altloc"] is None or isinstance(atom["altloc"], str) and len(atom["altloc"]) <= 1, "Invalid source alternate-location code")
        rkey, ckey = residue_key(atom), chain_key(atom)
        aid = (atom["model"], atom["source_atom_id"])
        site = (rkey, atom["atom_name"], atom["altloc"])
        require(aid not in atom_ids and site not in atom_sites, "Duplicate/ambiguous source atom identifier or alternate site")
        atom_ids.add(aid); atom_sites.add(site)
        if rkey not in residues:
            residues[rkey] = {**{field: atom[field] for field in RESIDUE_FIELDS}, "uid": f"res-{len(residues) + 1}",
                              "aa": STANDARD_AA.get(atom["residue_name"]), "atom_indices": [], "altlocs": []}
        residue = residues[rkey]
        atom["index"] = len(atom_ids) - 1; atom["residue_uid"] = residue["uid"]
        residue["atom_indices"].append(atom["index"])
        if atom["altloc"] not in residue["altlocs"]: residue["altlocs"].append(atom["altloc"])
        chains.setdefault(ckey, {field: atom[field] for field in CHAIN_FIELDS})
    return {"parser": {"name": "Gemmi", "version": gemmi.__version__}, "atoms": atoms,
            "residues": list(residues.values()), "chains": list(chains.values()), "models": sorted({a["model"] for a in atoms}, key=lambda m: (m is None, m or 0))}


def _validate_key(key, chain_only=False):
    fields(key, CHAIN_FIELDS if chain_only else RESIDUE_FIELDS, "structure source key")
    require(type(key["model"]) is int and key["model"] > 0, "Explicit positive model identifier required")
    for name in ("auth_chain", "label_asym"):
        require(key[name] is None or isinstance(key[name], str) and len(key[name]) <= 100, "Invalid source chain identifier")
    require(key["auth_chain"] is not None or key["label_asym"] is not None, "Source chain identifier missing")
    require(key["segment"] is None or isinstance(key["segment"], str) and len(key["segment"]) <= 100, "Source segment must retain text or unknown null")
    if not chain_only:
        for name in ("auth_number", "label_number"):
            require(key[name] is None or type(key[name]) is int and abs(key[name]) <= 2**53 - 1, "Invalid source residue number")
        require(key["auth_number"] is not None or key["label_number"] is not None, "Residue identifier missing")
        require(key["insertion_code"] is None or isinstance(key["insertion_code"], str) and len(key["insertion_code"]) <= 100, "Invalid insertion code")
        text(key["residue_name"], "source residue name", 100)


def validate_structure_shape(entity):
    identifier(entity["molecule_id"], "molecule")
    source(entity["source"], "structure.source")
    if entity["type"] == "structure":
        text(entity["name"], "structure.name", 500)
        require(entity["origin_kind"] in ("experimental", "computed", "unknown"), "Explicit structural origin kind required")
        text(entity["content"], "structure.content", MAX_TEXT)
        require(isinstance(entity["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", entity["sha256"]) is not None, "Source digest must be SHA-256")
        require(hashlib.sha256(entity["content"].encode("utf-8")).hexdigest() == entity["sha256"], "Coordinate source digest mismatch")
        parse_structure(entity["content"], entity["file_format"])
        return
    identifier(entity["structure_id"], "structure")
    require(isinstance(entity["chain_assignments"], list) and len(entity["chain_assignments"]) <= 10000, "Invalid chain assignment list")
    require(isinstance(entity["residues"], list) and len(entity["residues"]) <= 100000, "Invalid structure correspondence list")
    for assignment in entity["chain_assignments"]:
        fields(assignment, CHAIN_FIELDS | {"role", "molecule_chain_id", "target_ref", "label"}, "chain assignment")
        _validate_key({key: assignment[key] for key in CHAIN_FIELDS}, True)
        text(assignment["label"], "chain assignment label", 500)
        require(assignment["role"] in ("antibody", "antigen", "other"), "Unknown declared chain role")
        nullable_text(assignment["molecule_chain_id"], "assigned molecule chain")
        target = assignment["target_ref"]
        if target is not None:
            fields(target, {"namespace", "identifier"}, "target reference")
            text(target["namespace"], "target namespace", 200); text(target["identifier"], "target identifier", 500)
        require((assignment["role"] == "antibody" and assignment["molecule_chain_id"] is not None and target is None) or
                (assignment["role"] == "antigen" and target is not None and assignment["molecule_chain_id"] is None) or
                (assignment["role"] == "other" and target is None and assignment["molecule_chain_id"] is None), "Chain role requires explicit, consistent subject/target references")
    for entry in entity["residues"]:
        fields(entry, {"chain_id", "sequence_index", "status", "structure_residue", "altloc", "reason"}, "structure correspondence")
        text(entry["chain_id"], "molecule chain", 100)
        require(type(entry["sequence_index"]) is int and 1 <= entry["sequence_index"] <= 100000, "Explicit raw sequence index required")
        nullable_text(entry["reason"], "correspondence reason")
        require(isinstance(entry["altloc"], str) and len(entry["altloc"]) <= 1, "Explicit alternate conformer required")
        if entry["status"] == "mapped":
            _validate_key(entry["structure_residue"])
        else:
            require(entry["status"] == "unavailable" and entry["structure_residue"] is None and entry["altloc"] == "", "Unknown/invalid correspondence state")
            text(entry["reason"], "Unavailable mapping reason")


def validate_model_metric(entity):
    """Existing ipTM/pTM semantics, also used before source-row QC succeeds."""
    if entity['metric'].lower() in ('iptm', 'ptm'):
        require(entity['kind'] == 'computed' and entity['unit'] == '1', 'ipTM/pTM are dimensionless model-internal computed metrics')
        require(entity['value'] is None or 0 <= entity['value'] <= 1, 'ipTM/pTM value is outside its source-defined range')


def validate_structure_references(index):
    for entity in index.values():
        if entity["type"] == "structure":
            subject = index.get(entity["molecule_id"])
            require(subject is not None and subject["type"] == "molecule", "Unknown or wrong-type structure molecule")
        elif entity["type"] == "structure_map":
            structure, molecule = index.get(entity["structure_id"]), index.get(entity["molecule_id"])
            require(structure is not None and structure["type"] == "structure" and molecule is not None and molecule["type"] == "molecule", "Unknown structure or mapped molecule")
            require(structure["molecule_id"] == molecule["id"], "Structure correspondence names a different primary molecule")
            parsed = parse_structure(structure["content"], structure["file_format"])
            residues = {residue_key(r): r for r in parsed["residues"]}
            source_chains = {chain_key(c) for c in parsed["chains"]}
            molecule_chains = {c["id"]: c for c in molecule["chains"]}
            assignments = {}
            for assignment in entity["chain_assignments"]:
                key = chain_key(assignment)
                require(key in source_chains and key not in assignments, "Unknown or duplicate structural chain assignment")
                if assignment["role"] == "antibody": require(assignment["molecule_chain_id"] in molecule_chains, "Assigned molecule chain is unknown")
                assignments[key] = assignment
            seen_positions, seen_residues = set(), set()
            for entry in entity["residues"]:
                chain = molecule_chains.get(entry["chain_id"])
                require(chain is not None and entry["sequence_index"] <= len(chain["sequence"]), "Mapped sequence position unavailable in named chain")
                position = (entry["chain_id"], entry["sequence_index"])
                require(position not in seen_positions, "Duplicate molecule-chain sequence correspondence")
                seen_positions.add(position)
                if entry["status"] == "unavailable": continue
                rkey = residue_key(entry["structure_residue"])
                residue = residues.get(rkey)
                require(residue is not None, "Source structural residue unavailable")
                assignment = assignments.get(chain_key(residue))
                require(assignment is not None and assignment["role"] == "antibody" and assignment["molecule_chain_id"] == entry["chain_id"], "Mapped residue does not belong to its assigned antibody chain")
                require(residue["aa"] is not None and residue["aa"] == chain["sequence"][entry["sequence_index"] - 1], "Source residue and named sequence amino acid differ or residue is unsupported")
                conformers = {alt for alt in residue["altlocs"] if alt != ""}
                require(None not in conformers, "Unknown source conformer cannot be mapped")
                require(entry["altloc"] in conformers if conformers else entry["altloc"] == "", "Explicit available alternate conformer must be selected")
                target = tuple(entry["structure_residue"][key] for key in sorted(RESIDUE_FIELDS - {"residue_name"}))
                require(target not in seen_residues, "One structural residue locus cannot map to two sequence positions or alternatives")
                seen_residues.add(target)
        elif entity["type"] == "evidence":
            validate_model_metric(entity)
            subject = index.get(entity["subject_id"])
            if subject and subject["type"] == "structure" and entity["conditions"] is not None and "structure_model" in entity["conditions"]:
                model = entity["conditions"]["structure_model"]
                require(type(model) is int and model in parse_structure(subject["content"], subject["file_format"])["models"],
                        "Computed evidence names an unavailable structure model")


def structure_observation(bundle, structure_id, map_id=None):
    index = {e["id"]: e for e in bundle["entities"]}
    structure = index.get(structure_id)
    require(structure is not None and structure["type"] == "structure", "Unknown structure ID")
    parsed = parse_structure(structure["content"], structure["file_format"])
    maps = [e for e in bundle["entities"] if e["type"] == "structure_map" and e["structure_id"] == structure_id]
    selected = next((e for e in maps if e["id"] == map_id), None) if map_id else (maps[0] if len(maps) == 1 else None)
    require(map_id is None or selected is not None, "Selected structural correspondence is unavailable")
    return {"structure": {key: value for key, value in structure.items() if key != "content"}, "parsed": parsed,
            "map": selected, "map_options": [{"id": e["id"], "source": e["source"]} for e in maps],
            "confidence": [e for e in bundle["entities"] if e["type"] == "evidence" and e["subject_id"] == structure_id and e["kind"] == "computed"]}
