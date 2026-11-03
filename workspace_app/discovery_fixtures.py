"""Fixed J01 engineering inputs; not experimental antibodies or predictions.

The supplementary JSON is a user-imported file. It is never attached implicitly
to research data, and only accepts the exact fixture sequences and explicit class.
"""

import copy
import csv
import io

from .domain import SCHEMA, require
from .fixtures import STAMP, fixture_id, numbering_bundle


def sequence_input():
    fixture = numbering_bundle(800)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["external_id", "name", "sequence", "chain_role", "format"])
    for i, molecule in enumerate((e for e in fixture["entities"] if e["type"] == "molecule"), 1):
        writer.writerow([f"DISC-{i:03}", f"Discovery fixture candidate {i:03}", molecule["chains"][0]["sequence"],
                         "declared heavy variable chain (synthetic fixture)", "synthetic single variable chain"])
    writer.writerow(["DISC-MISSING", "Missing sequence fixture row", "", "", ""])
    writer.writerow(["DISC-INVALID", "Invalid sequence fixture row", "EVQ*", "", ""])
    return output.getvalue()


def support_bundle(imported):
    """Construct an explicit annotation/measurement file using imported IDs."""
    require(imported["project"].get("data_class") == "synthetic_fixture", "Discovery fixture requires explicit synthetic_fixture project metadata")
    molecules = [e for e in imported["entities"] if e["type"] == "molecule"]
    require(len(molecules) == 800, "Discovery fixture requires exactly 800 imported candidates")
    by_external = {m["external_id"]: m for m in molecules}
    template = numbering_bundle(800)
    template_molecules = [e for e in template["entities"] if e["type"] == "molecule"]
    template_maps = {e["molecule_id"]: e for e in template["entities"] if e["type"] == "residue_map" and e["chain_type"] == "heavy"}
    result = {"schema_version": SCHEMA, "project": copy.deepcopy(imported["project"]), "entities": []}
    project_id = imported["project"]["id"]

    def entity(entity_type, label, **values):
        record = {"id": fixture_id(entity_type, f"discovery/{project_id}/{label}"), "type": entity_type,
                  "project_id": project_id, "created_at": STAMP, **values}
        result["entities"].append(record)
        return record

    source = {"name": "SYNTHETIC J01 engineering binding dataset; not an experiment", "version": "1"}
    for i, template_molecule in enumerate(template_molecules):
        molecule = by_external.get(f"DISC-{i + 1:03}")
        require(molecule is not None and len(molecule["chains"]) == 1 and molecule["chains"][0]["sequence"] == template_molecule["chains"][0]["sequence"],
                "Only exact discovery fixture identities and sequences may receive synthetic annotations")
        annotation = copy.deepcopy(template_maps[template_molecule["id"]])
        annotation.update(id=fixture_id("residue_map", f"discovery/{project_id}/map-{i}"), project_id=project_id,
                          molecule_id=molecule["id"], chain_id=molecule["chains"][0]["id"])
        result["entities"].append(annotation)
        construct = entity("construct", f"construct-{i}", name=f"Discovery synthetic construct {i + 1}",
                           molecule_id=molecule["id"], cds=None, vector=None, signal_peptide=None)
        material = entity("material", f"material-{i}", name=f"Discovery synthetic material {i + 1}",
                          construct_id=construct["id"], lot=f"synthetic-{i + 1}")
        if i == 799:
            continue  # Separate not-measured from a registered null value.
        entity("evidence", f"evidence-{i}", subject_id=material["id"], kind="measured", metric="fixture_binding",
               source=copy.deepcopy(source), timestamp=STAMP,
               conditions=None if i == 2 else {"assay": "synthetic binding observation", "temperature_C": 25},
               value=None if i == 1 else float(i), unit="uM" if i == 3 else "nM")
        if i == 4:
            alternate = entity("material", "alternate-material", name="Discovery synthetic material 5 alternate lot",
                               construct_id=construct["id"], lot="synthetic-5-B")
            entity("evidence", "alternate-evidence", subject_id=alternate["id"], kind="measured", metric="fixture_binding",
                   source=copy.deepcopy(source), timestamp=STAMP, conditions={"assay": "synthetic binding observation", "temperature_C": 25},
                   value=4.5, unit="nM")
    return result
