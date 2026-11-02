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


def composition_bundle():
    """Two separate same-sequence units with explicit origins; no assembly claim."""
    from .composition import composition_signature
    bundle = example_bundle()
    remap = {bundle["project"]["id"]: fixture_id("project", "composition-project")}
    remap.update({e["id"]: fixture_id(e["type"], "composition/base/" + e["id"]) for e in bundle["entities"]})

    def namespaced(value):
        if isinstance(value, str):
            return remap.get(value, value)
        if isinstance(value, list):
            return [namespaced(item) for item in value]
        if isinstance(value, dict):
            return {key: namespaced(item) for key, item in value.items()}
        return value

    bundle = namespaced(bundle)
    bundle["project"]["title"] = "[SYNTHETIC FIXTURE] Explicit composition"
    parents = [e for e in bundle["entities"] if e["type"] == "molecule"][:2]
    units = []
    for i, parent in enumerate(parents):
        seq = parent["chains"][0]["sequence"]
        unit = {"id": fixture_id("binding_unit", f"composition-unit-{i}"), "type": "binding_unit",
                "project_id": bundle["project"]["id"], "created_at": STAMP, "name": f"Fixture binding unit {i + 1}",
                "topology": "single_chain", "source": {"name": "SYNTHETIC component fixture; no binding validation", "version": "1"},
                "chains": [{"id": "unit-chain", "role": "declared variable segment", "sequence": seq,
                            "origin": {"molecule_id": parent["id"], "chain_id": "chain-1", "start": 1, "end": len(seq)}}]}
        units.append(unit)
    def component(label, unit=None):
        return {"id": label, "role": "linker" if unit is None else "declared binding segment",
                "sequence": "GGS" if unit is None else unit["chains"][0]["sequence"],
                "origin": None if unit is None else {"binding_unit_id": unit["id"], "chain_id": "unit-chain", "start": 1,
                                                    "end": len(unit["chains"][0]["sequence"])}}
    first, linker, second, partner = component("unit-A", units[0]), component("linker"), component("unit-B", units[1]), component("partner-B", units[1])
    child = {"id": fixture_id("molecule", "composition-child"), "type": "molecule", "project_id": bundle["project"]["id"],
             "created_at": STAMP, "name": "Fixture tandem composition", "external_id": "COMP-001", "format": "declared tandem fixture",
             "source": {"name": "SYNTHETIC composition declaration; no assembly validation", "version": "1"},
             "chains": [{"id": "tandem", "role": "declared tandem", "sequence": first["sequence"] + linker["sequence"] + second["sequence"]},
                        {"id": "partner", "role": "declared partner", "sequence": partner["sequence"]}],
             "component_graph": {"chains": [{"chain_id": "tandem", "copies": 2, "components": [first, linker, second]},
                                               {"chain_id": "partner", "copies": 1, "components": [partner]}],
                                 "connections": [{"left": {"chain_id": "tandem", "component_id": "unit-A"},
                                                  "right": {"chain_id": "partner", "component_id": "partner-B"}, "kind": "declared_pairing"}]}}
    lineage = {"id": fixture_id("lineage", "composition-lineage"), "type": "lineage", "project_id": bundle["project"]["id"],
               "created_at": STAMP, "parent_id": parents[0]["id"], "child_id": child["id"],
               "change_set": {"kind": "composition", "reason": "Synthetic data consistency and origin-tracking test only.",
                              "before": composition_signature(parents[0]), "after": composition_signature(child)}}
    bundle["entities"].extend([*units, child, lineage])
    return bundle
