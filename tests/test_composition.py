"""F06: declared molecular identity and provenance. Synthetic engineering data."""

import copy

import pytest

from workspace_app.composition import composition_signature
from workspace_app.domain import ValidationError, new_id, validate_graph
from workspace_app.fixtures import composition_bundle, example_bundle
from workspace_app.storage import Store


def child(bundle):
    return next(e for e in bundle["entities"] if e["type"] == "molecule" and "component_graph" in e)


def test_order_copy_counts_unit_origins_lineage_restart_roundtrip(tmp_path):
    b = composition_bundle()
    s = Store(tmp_path / "original.sqlite3")
    s.import_bundle(b)
    restored = Store(s.path).bundle(b["project"]["id"])
    assert restored == b
    target = Store(tmp_path / "fresh.sqlite3"); target.import_bundle(restored)
    assert target.bundle(b["project"]["id"]) == b
    c = child(restored)
    assert [p["id"] for p in c["component_graph"]["chains"][0]["components"]] == ["unit-A", "linker", "unit-B"]
    assert [g["copies"] for g in c["component_graph"]["chains"]] == [2, 1]
    units = [e for e in restored["entities"] if e["type"] == "binding_unit"]
    assert units[0]["chains"][0]["sequence"] == units[1]["chains"][0]["sequence"]
    assert units[0]["id"] != units[1]["id"]
    sources = c["component_graph"]["chains"][0]["components"]
    assert sources[0]["origin"]["binding_unit_id"] != sources[2]["origin"]["binding_unit_id"]
    # No experiment/construct/material was fabricated for the new child.
    assert not any(e["type"] == "construct" and e["molecule_id"] == c["id"] for e in restored["entities"])
    assert not any(e["type"] == "evidence" and e["subject_id"] == c["id"] for e in restored["entities"])


def test_initial_and_composition_fixture_projects_coexist_without_id_reuse(tmp_path):
    store = Store(tmp_path / "coexist.sqlite3")
    initial, composed = example_bundle(), composition_bundle()
    store.import_bundle(initial); store.import_bundle(composed)
    assert len(store.projects()) == 2
    assert store.bundle(initial["project"]["id"]) == initial
    assert store.bundle(composed["project"]["id"]) == composed
    assert not ({e["id"] for e in initial["entities"]} & {e["id"] for e in composed["entities"]})


@pytest.mark.parametrize("case", ["undefined_chain", "duplicate_chain", "missing_chain", "empty_components", "duplicate_component",
                                  "order_mismatch", "zero_copies", "boolean_copies", "unknown_source", "source_range",
                                  "boolean_start", "source_sequence", "source_chain", "endpoint", "self_connection",
                                  "duplicate_reverse_connection", "unknown_kind", "unknown_graph_field", "null_graph"])
def test_invalid_component_graph_rejects_whole_import(tmp_path, case):
    b = composition_bundle(); c = child(b); graph = c["component_graph"]; chain = graph["chains"][0]
    component = chain["components"][0]; connection = graph["connections"][0]
    if case == "undefined_chain": chain["chain_id"] = "missing"
    elif case == "duplicate_chain": graph["chains"].append(copy.deepcopy(chain))
    elif case == "missing_chain": graph["chains"].pop()
    elif case == "empty_components": chain["components"] = []
    elif case == "duplicate_component": chain["components"][1]["id"] = component["id"]
    elif case == "order_mismatch": chain["components"].reverse(); chain["components"][0]["sequence"] = "ACD"
    elif case == "zero_copies": chain["copies"] = 0
    elif case == "boolean_copies": chain["copies"] = True
    elif case == "unknown_source": component["origin"]["binding_unit_id"] = new_id("binding_unit")
    elif case == "source_range": component["origin"]["end"] = 999
    elif case == "boolean_start": component["origin"]["start"] = True
    elif case == "source_sequence": component["origin"]["start"] = 2
    elif case == "source_chain": component["origin"]["chain_id"] = "missing"
    elif case == "endpoint": connection["left"]["component_id"] = "absent"
    elif case == "self_connection": connection["right"] = copy.deepcopy(connection["left"])
    elif case == "duplicate_reverse_connection": graph["connections"].append({"left": connection["right"], "right": connection["left"], "kind": connection["kind"]})
    elif case == "unknown_kind": connection["kind"] = "inferred"
    elif case == "unknown_graph_field": graph["inferred"] = True
    elif case == "null_graph": c["component_graph"] = None
    # Keep the snapshot synchronized so it cannot mask a graph validation failure.
    next(e for e in b["entities"] if e["type"] == "lineage")["change_set"]["after"] = composition_signature(c)
    store = Store(tmp_path / "test.sqlite3")
    with pytest.raises(ValidationError): store.import_bundle(b)
    assert store.projects() == []


@pytest.mark.parametrize("case", ["missing_topology", "wrong_count", "duplicate_chain", "origin_chain", "cross_project_origin", "provenance_cycle"])
def test_binding_unit_identity_and_origins_are_explicit(tmp_path, case):
    b = composition_bundle(); units = [e for e in b["entities"] if e["type"] == "binding_unit"]; unit = units[0]
    if case == "missing_topology": del unit["topology"]
    elif case == "wrong_count": unit["topology"] = "paired"
    elif case == "duplicate_chain": unit["topology"] = "paired"; unit["chains"] *= 2
    elif case == "origin_chain": unit["chains"][0]["origin"]["chain_id"] = "absent"
    elif case == "cross_project_origin": unit["chains"][0]["origin"]["molecule_id"] = new_id("molecule")
    elif case == "provenance_cycle":
        c = child(b)
        unit["chains"][0]["origin"] = {"molecule_id": c["id"], "chain_id": "tandem", "start": 1, "end": len(unit["chains"][0]["sequence"])}
    store = Store(tmp_path / "test.sqlite3")
    with pytest.raises(ValidationError): store.import_bundle(b)
    assert store.projects() == []


@pytest.mark.parametrize("case", ["self", "duplicate", "cycle", "before_mismatch", "after_boolean", "unknown_parent", "no_change", "unknown_kind"])
def test_lineage_exact_identity_diffs_and_acyclic_edges(tmp_path, case):
    b = composition_bundle(); line = next(e for e in b["entities"] if e["type"] == "lineage")
    if case == "self": line["child_id"] = line["parent_id"]
    elif case == "duplicate": extra = copy.deepcopy(line); extra["id"] = new_id("lineage"); b["entities"].append(extra)
    elif case == "cycle":
        extra = copy.deepcopy(line); extra["id"] = new_id("lineage")
        extra["parent_id"], extra["child_id"] = line["child_id"], line["parent_id"]
        extra["change_set"]["before"], extra["change_set"]["after"] = extra["change_set"]["after"], extra["change_set"]["before"]
        b["entities"].append(extra)
    elif case == "before_mismatch": line["change_set"]["before"]["format"] = "made up"
    elif case == "after_boolean": line["change_set"]["after"]["component_graph"]["chains"][1]["copies"] = True
    elif case == "unknown_parent": line["parent_id"] = new_id("molecule")
    elif case == "unknown_kind": line["change_set"]["kind"] = "inferred_humanization"
    elif case == "no_change":
        parent = next(e for e in b["entities"] if e["id"] == line["parent_id"])
        twin = copy.deepcopy(parent); twin["id"] = new_id("molecule"); twin["external_id"] = "TWIN"
        b["entities"].append(twin); line["child_id"] = twin["id"]; line["change_set"]["after"] = composition_signature(twin)
    store = Store(tmp_path / "test.sqlite3")
    with pytest.raises(ValidationError): store.import_bundle(b)
    assert store.projects() == []


def test_paired_unit_with_partial_origin_and_old_bundle_compatibility(tmp_path):
    old = example_bundle(); store = Store(tmp_path / "test.sqlite3"); store.import_bundle(old)
    parent = next(e for e in old["entities"] if e["type"] == "molecule")
    unit = {"id": new_id("binding_unit"), "type": "binding_unit", "project_id": old["project"]["id"],
            "created_at": parent["created_at"], "name": "Declared paired engineering fixture", "topology": "paired",
            "source": {"name": "Synthetic fixture", "version": None},
            "chains": [{"id": "one", "role": "declared first", "sequence": parent["chains"][0]["sequence"][1:5],
                        "origin": {"molecule_id": parent["id"], "chain_id": "chain-1", "start": 2, "end": 5}},
                       {"id": "two", "role": "declared second", "sequence": "ACDE", "origin": None}]}
    store.import_bundle({**old, "entities": [unit]})
    saved = store.bundle(old["project"]["id"])
    assert saved["entities"][:-1] == old["entities"]
    assert saved["entities"][-1] == unit
