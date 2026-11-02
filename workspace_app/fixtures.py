"""Synthetic engineering fixtures. Not scientific golden data or real predictions."""

import uuid

from .domain import PREFIX, SCHEMA

STAMP = "2026-11-02T00:00:00+00:00"


def fixture_id(kind, label):
    return PREFIX[kind] + "_" + str(uuid.uuid5(uuid.NAMESPACE_URL, "antibody-insight/fixture/" + label))


def example_bundle(count=8):
    project = {"id": fixture_id("project", "project-" + str(count)),
               "title": "[SYNTHETIC FIXTURE] Candidate study",
               "goal": "Engineering tests only; no experimentally validated antibodies or predictions.",
               "created_at": STAMP}
    entities = []

    def entity(entity_type, label, **values):
        result = {"id": fixture_id(entity_type, str(count) + "/" + label), "type": entity_type,
                  "project_id": project["id"], "created_at": STAMP, **values}
        entities.append(result)
        return result

    alphabet = "ACDEFGHIKLMNPQRSTVWY"
    for i in range(count):
        # Exact repeats are intentional; equal sequence does not imply equal molecule identity.
        suffix = "ACD" if i in (0, 1) else "".join(alphabet[(i // (20 ** j)) % 20] for j in range(3))
        molecule = entity("molecule", f"molecule-{i}", name=f"Fixture candidate {i + 1:03}",
                          external_id=f"FIX-{i + 1:03}", format="unspecified",
                          chains=[{"id": "chain-1", "role": "unknown", "sequence": "EVQLVESGGGLVQPGGSLRLSCAASGFTF" + suffix}],
                          source={"name": "SYNTHETIC FIXTURE generator", "version": "1"})
        if i < 8:
            construct = entity("construct", f"construct-{i}", name=f"Fixture construct {i + 1}",
                               molecule_id=molecule["id"], cds="GAA" * (i + 1), vector="fixture vector", signal_peptide=None)
            material = entity("material", f"material-{i}", name=f"Fixture material {i + 1}",
                              construct_id=construct["id"], lot=f"fixture-lot-{i + 1}")
            entity("evidence", f"measurement-{i}", subject_id=material["id"], kind="measured",
                   metric="fixture_binding", source={"name": "SYNTHETIC FIXTURE (not an actual experiment)", "version": "1"},
                   timestamp=STAMP, conditions=None if i == 2 else {"assay": "synthetic engineering test", "temperature_C": 25},
                   value=None if i == 1 else float(i), unit="nM")
            if i == 0:
                entity("evidence", "computed-0", subject_id=molecule["id"], kind="computed",
                       metric="fixture_metric (no predictive meaning)",
                       source={"name": "SYNTHETIC FIXTURE (no model executed)", "version": None},
                       timestamp=STAMP, conditions={"purpose": "label separation test"}, value=0.5, unit="1")
                alternate = entity("construct", "alternate-construct", name="Fixture alternate CDS",
                                   molecule_id=molecule["id"], cds="GAG", vector="fixture vector", signal_peptide="fixture signal")
                entity("material", "alternate-material", name="Fixture alternate lot", construct_id=alternate["id"], lot="fixture-lot-B")
    return {"schema_version": SCHEMA, "project": project, "entities": entities}
