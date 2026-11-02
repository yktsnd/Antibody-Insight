"""Explicit declared component relationships. P02/P05/P08, J02/J05/J08, F06.

This validates data consistency, not folding, pairing, chemistry or biological activity.
"""

from collections import deque
import copy
import json

from .domain import fields, identifier, json_value, require, sequence, source, text


def exact_json(left, right):
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def composition_signature(molecule):
    return copy.deepcopy({"format": molecule["format"], "chains": molecule["chains"],
                          "component_graph": molecule.get("component_graph")})


def interval_origin(origin, target):
    if origin is None:
        return
    fields(origin, {target + "_id", "chain_id", "start", "end"}, "origin")
    identifier(origin[target + "_id"], target)
    text(origin["chain_id"], "origin.chain_id", 100)
    require(type(origin["start"]) is int and type(origin["end"]) is int and
            1 <= origin["start"] <= origin["end"] <= 100000, "Origin requires an inclusive 1-based sequence interval")


def validate_composition_entity(entity):
    if entity["type"] == "binding_unit":
        text(entity["name"], "binding_unit.name", 500)
        require(entity["topology"] in ("paired", "single_chain"), "Binding-unit topology must be explicitly declared")
        source(entity["source"], "binding_unit.source")
        chains = entity["chains"]
        count = 2 if entity["topology"] == "paired" else 1
        require(isinstance(chains, list) and len(chains) == count, "Binding-unit chain count does not match declared topology")
        ids = set()
        for chain in chains:
            fields(chain, {"id", "role", "sequence", "origin"}, "binding_unit.chain")
            text(chain["id"], "binding_unit.chain.id", 100)
            require(chain["id"] not in ids, "Duplicate binding-unit chain ID")
            ids.add(chain["id"])
            text(chain["role"], "binding_unit.chain.role", 100)
            sequence(chain["sequence"], "binding_unit.chain.sequence")
            interval_origin(chain["origin"], "molecule")
    else:
        identifier(entity["parent_id"], "molecule")
        identifier(entity["child_id"], "molecule")
        require(entity["parent_id"] != entity["child_id"], "Lineage cannot reference itself")
        change = entity["change_set"]
        fields(change, {"kind", "reason", "before", "after"}, "change_set")
        require(change["kind"] == "composition", "Unsupported lineage change-set kind")
        text(change["reason"], "change_set.reason")
        for key in ("before", "after"):
            fields(change[key], {"format", "chains", "component_graph"}, "change_set." + key)
            json_value(change[key], "change_set." + key)


def validate_component_graph_shape(molecule):
    if "component_graph" not in molecule:
        return
    graph = molecule["component_graph"]
    fields(graph, {"chains", "connections"}, "component_graph")
    require(isinstance(graph["chains"], list) and 0 < len(graph["chains"]) <= 100, "Component graph requires defined chains")
    chain_index = {chain["id"]: chain for chain in molecule["chains"]}
    graph_ids, component_ids, endpoints = set(), set(), set()
    for chain in graph["chains"]:
        fields(chain, {"chain_id", "copies", "components"}, "component_graph.chain")
        text(chain["chain_id"], "component_graph.chain.chain_id", 100)
        require(chain["chain_id"] in chain_index and chain["chain_id"] not in graph_ids,
                "Undefined or duplicate graph chain")
        graph_ids.add(chain["chain_id"])
        require(type(chain["copies"]) is int and 1 <= chain["copies"] <= 100, "Explicit integer chain copy count required (1–100)")
        require(isinstance(chain["components"], list) and 0 < len(chain["components"]) <= 1000,
                "Ordered non-empty component list required")
        assembled = []
        for component in chain["components"]:
            fields(component, {"id", "role", "sequence", "origin"}, "component")
            text(component["id"], "component.id", 100)
            require(component["id"] not in component_ids, "Duplicate component ID within molecule")
            component_ids.add(component["id"])
            endpoints.add((chain["chain_id"], component["id"]))
            text(component["role"], "component.role", 100)
            sequence(component["sequence"], "component.sequence")
            interval_origin(component["origin"], "binding_unit")
            assembled.append(component["sequence"])
        require("".join(assembled) == chain_index[chain["chain_id"]]["sequence"], "Component order/sequence differs from molecule chain")
    require(graph_ids == set(chain_index), "Every molecule chain must have an explicit graph definition")
    connections = graph["connections"]
    require(isinstance(connections, list) and len(connections) <= 5000, "Invalid connection list")
    seen = set()
    for connection in connections:
        fields(connection, {"left", "right", "kind"}, "connection")
        pair = []
        for side in ("left", "right"):
            endpoint = connection[side]
            fields(endpoint, {"chain_id", "component_id"}, "connection." + side)
            text(endpoint["chain_id"], "endpoint.chain_id", 100)
            text(endpoint["component_id"], "endpoint.component_id", 100)
            key = (endpoint["chain_id"], endpoint["component_id"])
            require(key in endpoints, "Connection endpoint is not defined")
            pair.append(key)
        require(pair[0] != pair[1], "Connection cannot join an endpoint to itself")
        require(connection["kind"] in ("covalent", "disulfide", "noncovalent", "declared_pairing"), "Unsupported declared connection kind")
        signature = tuple(sorted(pair)) + (connection["kind"],)
        require(signature not in seen, "Duplicate declared connection")
        seen.add(signature)


def acyclic(edges, label):
    """Iterative DAG check so a long imported lineage cannot overflow recursion."""
    outgoing, degree = {}, {}
    for left, right in edges:
        outgoing.setdefault(left, set()).add(right)
        degree.setdefault(left, 0)
        degree.setdefault(right, 0)
    for targets in outgoing.values():
        for target in targets:
            degree[target] += 1
    ready = deque(node for node, count in degree.items() if count == 0)
    visited = 0
    while ready:
        node = ready.popleft(); visited += 1
        for target in outgoing.get(node, ()):
            degree[target] -= 1
            if degree[target] == 0:
                ready.append(target)
    require(visited == len(degree), f"{label} cycle rejected")


def validate_composition_references(index):
    provenance_edges, lineage_edges = [], set()

    def resolve_origin(origin, kind, declared_sequence):
        key = origin[kind + "_id"]
        target = index.get(key)
        require(target is not None and target["type"] == kind, f"Unknown or wrong-type {kind} origin")
        chain = next((c for c in target["chains"] if c["id"] == origin["chain_id"]), None)
        require(chain is not None, "Origin chain is not defined")
        require(origin["end"] <= len(chain["sequence"]), "Origin interval exceeds source chain")
        require(chain["sequence"][origin["start"] - 1:origin["end"]] == declared_sequence,
                "Declared component sequence differs from source interval")
        return key

    for entity in index.values():
        if entity["type"] == "binding_unit":
            for chain in entity["chains"]:
                if chain["origin"] is not None:
                    key = resolve_origin(chain["origin"], "molecule", chain["sequence"])
                    provenance_edges.append((entity["id"], key))
        elif entity["type"] == "molecule" and "component_graph" in entity:
            for chain in entity["component_graph"]["chains"]:
                for component in chain["components"]:
                    if component["origin"] is not None:
                        key = resolve_origin(component["origin"], "binding_unit", component["sequence"])
                        provenance_edges.append((entity["id"], key))
        elif entity["type"] == "lineage":
            parent, child = index.get(entity["parent_id"]), index.get(entity["child_id"])
            require(parent is not None and child is not None and parent["type"] == child["type"] == "molecule",
                    "Unknown or wrong-type lineage molecule")
            edge = (parent["id"], child["id"])
            require(edge not in lineage_edges, "Duplicate parent/child lineage edge")
            lineage_edges.add(edge)
            change = entity["change_set"]
            require(exact_json(change["before"], composition_signature(parent)) and
                    exact_json(change["after"], composition_signature(child)),
                    "Lineage before/after does not match the named molecules")
            require(not exact_json(change["before"], change["after"]), "Lineage must describe an actual composition change")
    acyclic(provenance_edges, "Composition provenance")
    acyclic(lineage_edges, "Lineage")
