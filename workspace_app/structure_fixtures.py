"""Synthetic coordinate fixtures, no real structure/model prediction or human goldens."""

import copy
import hashlib

from .domain import SCHEMA
from .fixtures import STAMP, fixture_id
from .structures import RESIDUE_FIELDS, parse_structure


def structure_bundle():
    project = {"id": fixture_id("project", "structures"), "title": "[SYNTHETIC FIXTURE] Structural observation",
               "goal": "Coordinate/correspondence engineering tests only; no biological interpretation", "created_at": STAMP, "data_class": "synthetic_fixture"}
    entities = []
    for candidate_index in range(2):
        molecule = {"id": fixture_id("molecule", f"structure-candidate-{candidate_index}"), "type": "molecule", "project_id": project["id"],
                    "created_at": STAMP, "name": f"Structural fixture candidate {candidate_index + 1}", "external_id": f"STR-{candidate_index + 1:03}",
                    "format": "declared synthetic fragment", "source": {"name": "SYNTHETIC sequence fixture", "version": "1"},
                    "chains": [{"id": "H", "role": "declared antibody fragment", "sequence": "ACDEFG"},
                               {"id": "L", "role": "declared partner fragment", "sequence": "GH"}]}
        entities.append(molecule)
        rows = []
        # Missing sequence index3 is intentional. H3A is index4; H4 has A/B alternates.
        residues = [("H",1,"","ALA",0,0), ("H",2,"","CYS",4,1), ("H",3,"A","GLU",8,0),
                    ("H",4,"","PHE",12,1), ("H",5,"","GLY",16,0),
                    ("L",1,"","GLY",2,8), ("L",2,"","HIS",6,9),
                    ("T",1,"","TYR",5,-8), ("T",2,"","THR",9,-9), ("T",3,"","THR",13,-8)]
        for model in (1,2):
            for role, number, ins, name, x, y in residues:
                for alt in (["A","B"] if role == "H" and number == 4 else [""]):
                    rows.append({"model": model, "role": role, "number": number, "ins": ins, "name": name, "alt": alt,
                                 "x": x + candidate_index * .3, "y": y + (1 if alt == "B" else 0), "z": model * 2 + (number % 2)})
        if candidate_index == 0:
            lines = []
            for model in (1,2):
                lines.append(f"MODEL     {model:4d}")
                for serial, row in enumerate((r for r in rows if r["model"] == model), 1):
                    lines.append(f"ATOM  {serial:5d}  CA {row['alt'] or ' '}{row['name']:>3} {row['role']}{row['number']:4d}{row['ins'] or ' '}   {row['x']:8.3f}{row['y']:8.3f}{row['z']:8.3f}{1.:6.2f}{88.:6.2f}           C  ")
                lines.append("ENDMDL")
            content, file_format = "\n".join(lines) + "\nEND\n", "pdb"
        else:
            tags = "group_PDB id type_symbol label_atom_id label_alt_id label_comp_id label_asym_id label_seq_id pdbx_PDB_ins_code Cartn_x Cartn_y Cartn_z occupancy B_iso_or_equiv auth_seq_id auth_comp_id auth_asym_id pdbx_PDB_model_num".split()
            lines = ["data_synthetic", "loop_", *("_atom_site." + tag for tag in tags)]
            for serial, row in enumerate(rows, 1):
                role = row["role"]
                label_number = row["number"] + (1 if role == "H" and row["number"] >= 3 else 0)
                values = ["ATOM", str(serial), "C", "CA", row["alt"] or ".", row["name"], {"H":"VH","L":"VL","T":"AG"}[role], str(label_number), row["ins"] or ".",
                          str(row["x"]), str(row["y"]), str(row["z"]), "?", ".", str(row["number"] + 100), row["name"], role + "-author", str(row["model"])]
                lines.append(" ".join(values))
            content, file_format = "\n".join(lines) + "\n", "mmcif"
        structure = {"id": fixture_id("structure", f"coordinate-file-{candidate_index}"), "type": "structure", "project_id": project["id"],
                     "created_at": STAMP, "name": f"Synthetic complex {candidate_index + 1}.{file_format}", "molecule_id": molecule["id"],
                     "file_format": file_format, "content": content, "sha256": hashlib.sha256(content.encode()).hexdigest(), "origin_kind": "computed",
                     "source": {"name": "SYNTHETIC coordinate generator; no prediction model executed", "version": "1"}}
        entities.append(structure)
        parsed = parse_structure(content, file_format)
        for model in (1,2):
            assignments = []
            for chain in (c for c in parsed["chains"] if c["model"] == model):
                original = (chain["auth_chain"] or "")[0]
                assignments.append({**chain, "role": "antigen" if original == "T" else "antibody", "molecule_chain_id": None if original == "T" else original,
                                    "target_ref": {"namespace": "synthetic-fixture", "identifier": "TARGET-001"} if original == "T" else None,
                                    "label": "Declared same synthetic antigen" if original == "T" else f"Declared antibody {original}"})
            entries = []
            for residue in (r for r in parsed["residues"] if r["model"] == model):
                role = residue["auth_chain"][0]
                if role == "T": continue
                auth_number = residue["auth_number"] - (100 if candidate_index else 0)
                sequence_index = auth_number + (1 if role == "H" and auth_number >= 3 else 0)
                entries.append({"chain_id": role, "sequence_index": sequence_index, "status": "mapped",
                                "structure_residue": {key: residue[key] for key in RESIDUE_FIELDS},
                                "altloc": "A" if role == "H" and auth_number == 4 else "", "reason": None})
            entries.append({"chain_id": "H", "sequence_index": 3, "status": "unavailable", "structure_residue": None, "altloc": "", "reason": "No coordinates in synthetic source"})
            entities.append({"id": fixture_id("structure_map", f"map-{candidate_index}-{model}"), "type": "structure_map", "project_id": project["id"],
                             "created_at": STAMP, "structure_id": structure["id"], "molecule_id": molecule["id"],
                             "source": {"name": "SYNTHETIC explicit correspondence; not a validated biological mapping", "version": "1"},
                             "chain_assignments": assignments, "residues": entries})
            if candidate_index == 0:
                entities.append({"id": fixture_id("evidence", f"structure-metric-{model}"), "type": "evidence", "project_id": project["id"], "created_at": STAMP,
                                 "subject_id": structure["id"], "kind": "computed", "metric": "ipTM", "source": {"name": "SYNTHETIC metric; no AlphaFold run", "version": "1"},
                                 "timestamp": STAMP, "conditions": {"structure_model": model, "purpose": "synthetic model-scope check"}, "value": .82 if model == 1 else .66, "unit": "1"})
    return {"schema_version": SCHEMA, "project": project, "entities": entities}
