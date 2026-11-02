"""Independent F06 contract replay; all values are engineering fixtures."""

import copy

import pytest

from workspace_app.adapters import new_project
from workspace_app.composition import composition_signature
from workspace_app.domain import SCHEMA, ValidationError, new_id
from workspace_app.fixtures import composition_bundle, example_bundle
from workspace_app.storage import Store


def graph_molecule(bundle):
    return next(e for e in bundle["entities"] if e["type"] == "molecule" and "component_graph" in e)


def synchronize_signature(bundle):
    molecule = graph_molecule(bundle)
    next(e for e in bundle["entities"] if e["type"] == "lineage")["change_set"]["after"] = composition_signature(molecule)


def test_both_explicit_fixture_projects_can_coexist_without_reusing_entity_ids(tmp_path):
    store = Store(tmp_path / "two-projects.sqlite3")
    old, composed = example_bundle(), composition_bundle()
    assert {e["id"] for e in old["entities"]}.isdisjoint({e["id"] for e in composed["entities"]})
    store.import_bundle(old)
    store.import_bundle(composed)
    assert store.bundle(old["project"]["id"]) == old
    assert store.bundle(composed["project"]["id"]) == composed


def test_component_endpoint_chain_scope_is_not_replaced_by_global_component_match(tmp_path):
    bundle = composition_bundle()
    molecule = graph_molecule(bundle)
    molecule["component_graph"]["connections"][0]["left"]["chain_id"] = "partner"
    synchronize_signature(bundle)
    store = Store(tmp_path / "endpoint.sqlite3")
    with pytest.raises(ValidationError, match="endpoint"):
        store.import_bundle(bundle)
    assert store.projects() == []


def test_true_cross_project_unit_origin_is_rejected_without_mutating_existing_data(tmp_path):
    old, bundle = example_bundle(9), composition_bundle()
    store = Store(tmp_path / "cross-project.sqlite3")
    store.import_bundle(old)
    foreign = next(e for e in old["entities"] if e["type"] == "molecule")
    unit = next(e for e in bundle["entities"] if e["type"] == "binding_unit")
    unit["chains"][0]["origin"]["molecule_id"] = foreign["id"]
    with pytest.raises(ValidationError, match="origin"):
        store.import_bundle(bundle)
    assert store.projects() == [old["project"]]
    assert store.bundle(old["project"]["id"]) == old


@pytest.mark.parametrize("field,value", [("start", 0), ("end", False), ("start", 1.0), ("end", 32.0)])
def test_intervals_do_not_coerce_zero_bool_or_float_into_indexes(tmp_path, field, value):
    bundle = composition_bundle()
    unit = next(e for e in bundle["entities"] if e["type"] == "binding_unit")
    unit["chains"][0]["origin"][field] = value
    store = Store(tmp_path / "indexes.sqlite3")
    with pytest.raises(ValidationError):
        store.import_bundle(bundle)
    assert store.projects() == []


def test_exact_last_residue_origin_and_max_copy_count_roundtrip(tmp_path):
    bundle = composition_bundle()
    molecule = graph_molecule(bundle)
    units = [e for e in bundle["entities"] if e["type"] == "binding_unit"]
    # Add an explicit one-residue unit referencing exactly the last source residue.
    unit = copy.deepcopy(units[0])
    unit["id"] = new_id("binding_unit")
    origin = unit["chains"][0]["origin"]
    origin["start"] = origin["end"]
    unit["chains"][0]["sequence"] = unit["chains"][0]["sequence"][-1]
    bundle["entities"].append(unit)
    component = molecule["component_graph"]["chains"][1]["components"][0]
    component["sequence"] = unit["chains"][0]["sequence"]
    component["origin"] = {"binding_unit_id": unit["id"], "chain_id": unit["chains"][0]["id"], "start": 1, "end": 1}
    molecule["chains"][1]["sequence"] = component["sequence"]
    molecule["component_graph"]["chains"][1]["copies"] = 100
    synchronize_signature(bundle)
    store = Store(tmp_path / "boundary.sqlite3")
    store.import_bundle(bundle)
    assert Store(store.path).bundle(bundle["project"]["id"]) == bundle


def test_equal_sequence_origin_substitution_in_lineage_snapshot_is_not_equivalent(tmp_path):
    bundle = composition_bundle()
    units = [e for e in bundle["entities"] if e["type"] == "binding_unit"]
    assert units[0]["chains"][0]["sequence"] == units[1]["chains"][0]["sequence"]
    line = next(e for e in bundle["entities"] if e["type"] == "lineage")
    line["change_set"]["after"]["component_graph"]["chains"][0]["components"][0]["origin"]["binding_unit_id"] = units[1]["id"]
    store = Store(tmp_path / "exact-origin.sqlite3")
    with pytest.raises(ValidationError, match="before/after"):
        store.import_bundle(bundle)
    assert store.projects() == []


def dependency_chain(depth):
    project = new_project("SYNTHETIC deep dependencies", "Iterative provenance/lineage validation only")
    entities = []
    def entity(kind, **values):
        result = {"id": new_id(kind), "type": kind, "project_id": project["id"], "created_at": project["created_at"], **values}
        entities.append(result)
        return result
    source = {"name": "SYNTHETIC independent fixture", "version": None}
    previous = entity("molecule", name="base", external_id="base", format="unspecified", source=source,
                      chains=[{"id": "C", "role": "unknown", "sequence": "A"}])
    for i in range(depth):
        unit = entity("binding_unit", name=f"unit-{i}", topology="single_chain", source=source,
                      chains=[{"id": "C", "role": "unknown", "sequence": "A", "origin": {
                          "molecule_id": previous["id"], "chain_id": "C", "start": 1, "end": 1}}])
        current = entity("molecule", name=f"child-{i}", external_id=f"child-{i}", format="unspecified", source=source,
                         chains=[{"id": "C", "role": "unknown", "sequence": "A"}], component_graph={
                             "chains": [{"chain_id": "C", "copies": 1, "components": [{"id": "P", "role": "declared", "sequence": "A", "origin": {
                                 "binding_unit_id": unit["id"], "chain_id": "C", "start": 1, "end": 1}}]}], "connections": []})
        entity("lineage", parent_id=previous["id"], child_id=current["id"], change_set={
            "kind": "composition", "reason": "SYNTHETIC origin change", "before": composition_signature(previous), "after": composition_signature(current)})
        previous = current
    return {"schema_version": SCHEMA, "project": project, "entities": entities}


def test_1100_level_provenance_and_lineage_dags_import_without_recursion_and_roundtrip(tmp_path):
    bundle = dependency_chain(1100)
    bundle["entities"].reverse()  # All references are forward in input order.
    store = Store(tmp_path / "deep.sqlite3")
    store.import_bundle(bundle)
    assert Store(store.path).bundle(bundle["project"]["id"]) == bundle


def test_late_provenance_cycle_in_long_graph_rejects_whole_batch(tmp_path):
    bundle = dependency_chain(1100)
    first_unit = next(e for e in bundle["entities"] if e["type"] == "binding_unit")
    last_molecule = [e for e in bundle["entities"] if e["type"] == "molecule"][-1]
    first_unit["chains"][0]["origin"]["molecule_id"] = last_molecule["id"]
    store = Store(tmp_path / "late-cycle.sqlite3")
    with pytest.raises(ValidationError, match="cycle"):
        store.import_bundle(bundle)
    assert store.projects() == []


@pytest.mark.parametrize("entity_type", ["binding_unit", "lineage"])
def test_unknown_fields_on_new_entity_types_fail_before_write(tmp_path, entity_type):
    bundle = composition_bundle()
    next(e for e in bundle["entities"] if e["type"] == entity_type)["invented_science"] = True
    store = Store(tmp_path / "unknown.sqlite3")
    with pytest.raises(ValidationError) as error:
        store.import_bundle(bundle)
    assert error.value.details == ["entity.invented_science"]
    assert store.projects() == []
