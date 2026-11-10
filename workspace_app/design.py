"""Explicit source-numbered substitutions; no numbering or biological prediction.

F10: P02/P04, J02/J04, AC-J02/AC-J04.
"""

from __future__ import annotations

import copy

from . import __version__
from .composition import composition_signature, exact_json
from .domain import SCHEMA, fields, identifier, json_value, new_id, now, require, text, validate_extension
from .numbering import coordinate_key, observe_map, region_for

TARGETS = frozenset("ACDEFGHIKLMNPQRSTVWY")
REQUEST_FIELDS = {"parent_map_id", "number", "ins_code", "to_aa", "reference_map_id"}
MUTATION_FIELDS = REQUEST_FIELDS | {"chain_id", "domain_id", "scheme", "sequence_index", "from_aa", "region"}


def eligible_map(index, project, map_id, molecule_id=None):
    identifier(map_id, "residue_map")
    record = index.get(map_id)
    require(record is not None and record["type"] == "residue_map", "Numbering map is unavailable")
    require(molecule_id is None or record["molecule_id"] == molecule_id, "Numbering map belongs to another molecule")
    require(observe_map(record, project)["eligible"], "Numbering unavailable, failed or unverified; no substitution authorized")
    return record


def reference_map(index, project, parent_map, map_id):
    if map_id is None:
        return None
    record = eligible_map(index, project, map_id)
    require(all(record[key] == parent_map[key] for key in ("scheme", "definition", "chain_type")),
            "Reference map uses a different scheme, domain definition or chain type")
    return record


def coordinate(number, ins_code):
    require(type(number) is int and 1 <= number <= 129, "Number must be an integer source coordinate")
    require(isinstance(ins_code, str), "Insertion code must remain exact text")


def design_context(bundle, parent_id, map_id, reference_map_id=None):
    index = {e["id"]: e for e in bundle["entities"]}
    require(isinstance(parent_id, str) and parent_id in index and index[parent_id]["type"] == "molecule", "Unknown parent molecule")
    parent = eligible_map(index, bundle["project"], map_id, parent_id)
    reference = reference_map(index, bundle["project"], parent, reference_map_id)
    left = {(entry["number"], entry["ins_code"]): entry for entry in parent["entries"]}
    right = {(entry["number"], entry["ins_code"]): entry for entry in reference["entries"]} if reference else {}
    rows = [{"number": number, "ins_code": ins_code, "coordinate": str(number) + ins_code,
             "region": region_for(number), "parent": left.get((number, ins_code)), "reference": right.get((number, ins_code))}
            for number, ins_code in sorted(left.keys() | right.keys(), key=lambda pair: coordinate_key(*pair))]
    counts = lambda entries: {region: sum(region_for(e["number"]) == region for e in entries) for region in ("CDR1", "CDR2", "CDR3")}
    parent_counts = counts(parent["entries"])
    reference_counts = counts(reference["entries"]) if reference else None
    return {"parent_map": observe_map(parent, bundle["project"]),
            "reference_map": observe_map(reference, bundle["project"]) if reference else None, "rows": rows,
            "parent_observed_cdr_counts": parent_counts, "reference_observed_cdr_counts": reference_counts,
            "different_observed_cdr_counts": reference is not None and parent_counts != reference_counts,
            "comparison_scope": "Recorded-coordinate comparison only; not inferred alignment, homology or human classification."}


def resolve_mutation(request, parent, index, project):
    fields(request, REQUEST_FIELDS, "substitution")
    coordinate(request["number"], request["ins_code"])
    require(isinstance(request["to_aa"], str) and len(request["to_aa"]) == 1 and request["to_aa"] in TARGETS,
            "Substitution target must be one of the 20 canonical amino acids; other targets unsupported")
    record = eligible_map(index, project, request["parent_map_id"], parent["id"])
    reference_map(index, project, record, request["reference_map_id"])
    entry = next((entry for entry in record["entries"] if (entry["number"], entry["ins_code"]) == (request["number"], request["ins_code"])), None)
    require(entry is not None, "Coordinate mapping unavailable; no neighbouring or raw-index fallback")
    chain = next((chain for chain in parent["chains"] if chain["id"] == record["chain_id"]), None)
    require(chain is not None and 1 <= entry["sequence_index"] <= len(chain["sequence"]) and chain["sequence"][entry["sequence_index"] - 1] == entry["aa"],
            "Source map does not match the actual parent chain/index/amino acid")
    require(entry["aa"] != request["to_aa"], "Unchanged residue is not a substitution")
    return {**request, "chain_id": record["chain_id"], "domain_id": record["domain_id"], "scheme": record["scheme"],
            "sequence_index": entry["sequence_index"], "from_aa": entry["aa"], "region": region_for(entry["number"])}


def apply_substitutions(parent, mutations):
    """Copy every unmodified declaration and explicitly drop invalid exact origins."""
    result = copy.deepcopy(parent)
    seen = set()
    for mutation in mutations:
        key = mutation["chain_id"], mutation["sequence_index"]
        require(key not in seen, "Duplicate source residue in substitution list")
        seen.add(key)
        chain = next(c for c in result["chains"] if c["id"] == mutation["chain_id"])
        offset = mutation["sequence_index"] - 1
        require(chain["sequence"][offset] == mutation["from_aa"], "Substitution before-residue differs from parent")
        chain["sequence"] = chain["sequence"][:offset] + mutation["to_aa"] + chain["sequence"][offset + 1:]
    for graph_chain in result.get("component_graph", {}).get("chains", []):
        chain = next(c for c in result["chains"] if c["id"] == graph_chain["chain_id"])
        start = 0
        for component in graph_chain["components"]:
            end = start + len(component["sequence"])
            new_sequence = chain["sequence"][start:end]
            if component["sequence"] != new_sequence:
                component["sequence"] = new_sequence
                component["origin"] = None
            start = end
    return result


def validate_substitution_shape(change):
    fields(change, {"kind", "reason", "before", "after", "mutations"}, "substitution change_set")
    text(change["reason"], "change_set.reason")
    for key in ("before", "after"):
        fields(change[key], {"format", "chains", "component_graph"}, "change_set." + key)
        json_value(change[key], "change_set." + key)
    require(isinstance(change["mutations"], list) and 0 < len(change["mutations"]) <= 1000, "A substitution design requires 1–1000 changes")
    for mutation in change["mutations"]:
        fields(mutation, MUTATION_FIELDS, "mutation")
        identifier(mutation["parent_map_id"], "residue_map")
        if mutation["reference_map_id"] is not None:
            identifier(mutation["reference_map_id"], "residue_map")
        coordinate(mutation["number"], mutation["ins_code"])
        require(type(mutation["sequence_index"]) is int and mutation["sequence_index"] > 0, "Mutation raw index must be an integer")
        for key in ("chain_id", "domain_id", "scheme", "from_aa", "to_aa", "region"):
            text(mutation[key], "mutation." + key, 100)


def validate_substitution_references(parent, child, change, index, project):
    canonical = [resolve_mutation({key: mutation[key] for key in REQUEST_FIELDS}, parent, index, project) for mutation in change["mutations"]]
    require(exact_json(canonical, change["mutations"]), "Mutation identity differs from its named parent source map")
    expected = apply_substitutions(parent, canonical)
    require(exact_json(composition_signature(expected), composition_signature(child)),
            "Child differs from the declared substitutions, chain roles, component origins or topology")


def variant_preview(bundle, parent_id, name, external_id, reason, substitutions):
    index = {e["id"]: e for e in bundle["entities"]}
    require(isinstance(parent_id, str) and parent_id in index and index[parent_id]["type"] == "molecule", "Unknown parent molecule")
    require(isinstance(substitutions, list) and 0 < len(substitutions) <= 1000, "Choose 1–1000 substitutions")
    text(name, "Child name", 500); text(external_id, "Child external ID", 500); text(reason, "Design reason")
    parent = index[parent_id]
    mutations = [resolve_mutation(request, parent, index, bundle["project"]) for request in substitutions]
    child = apply_substitutions(parent, mutations)
    stamp = now()
    child.update(id=new_id("molecule"), name=name, external_id=external_id, created_at=stamp,
                 source={"name": "Antibody Insight explicit substitution design", "version": __version__})
    lineage = {"id": new_id("lineage"), "type": "lineage", "project_id": bundle["project"]["id"], "created_at": stamp,
               "parent_id": parent_id, "child_id": child["id"], "change_set": {"kind": "substitution", "reason": reason,
               "before": composition_signature(parent), "after": composition_signature(child), "mutations": mutations}}
    validate_extension(bundle["project"], bundle["entities"], [child, lineage])
    return {"schema_version": SCHEMA, "project": copy.deepcopy(bundle["project"]), "entities": [child, lineage]}
