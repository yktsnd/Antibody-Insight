"""Researcher-authored proposed claims, separate from observations and decisions.

F11: P02/P03/P04/P06, J02/J03/J04/J06 and their acceptance criteria.
"""

from __future__ import annotations

import copy

from . import __version__
from .domain import SCHEMA, fields, identifier, json_value, molecule_id_for, new_id, now, nullable_text, require, source, text, validate_extension


def id_list(value, kind, label, nonempty=False):
    require(isinstance(value, list) and (not nonempty or bool(value)) and len(value) <= 1000, label + " must be a list of up to 1000 IDs")
    for key in value:
        identifier(key, kind)
    require(len(set(value)) == len(value), "Duplicate " + label)


def validate_hypothesis_shape(record):
    text(record["text"], "Hypothesis text")
    text(record["question"], "Next experiment / question")
    nullable_text(record["limitations"], "Hypothesis limitations")
    require(record["status"] == "proposed", "Only proposed research hypotheses are supported; no validation inferred")
    source(record["source"], "hypothesis.source")
    for key, kind in (("molecule_ids", "molecule"), ("related_evidence_ids", "evidence"), ("lineage_ids", "lineage")):
        id_list(record[key], kind, key, nonempty=key == "molecule_ids")
    require(isinstance(record["residue_refs"], list) and len(record["residue_refs"]) <= 1000, "Residue references must be a list")
    seen = set()
    for ref in record["residue_refs"]:
        fields(ref, {"molecule_id", "chain_id", "sequence_index"}, "hypothesis residue")
        identifier(ref["molecule_id"], "molecule"); text(ref["chain_id"], "residue chain", 100)
        require(type(ref["sequence_index"]) is int and 1 <= ref["sequence_index"] <= 100000, "Residue raw index must be a 1-based integer")
        key = ref["molecule_id"], ref["chain_id"], ref["sequence_index"]
        require(key not in seen, "Duplicate hypothesis residue reference"); seen.add(key)
    require(isinstance(record["structure_refs"], list) and len(record["structure_refs"]) <= 100, "Structural contexts must be a list")
    seen = set()
    for ref in record["structure_refs"]:
        fields(ref, {"structure_id", "model", "structure_map_id"}, "hypothesis structure", {"residue"})
        identifier(ref["structure_id"], "structure")
        require(ref["model"] is None or type(ref["model"]) is int, "Structural model must be its actual integer identity or null")
        if ref["structure_map_id"] is not None:
            identifier(ref["structure_map_id"], "structure_map")
        key = ref["structure_id"], ref["model"], ref["structure_map_id"]
        require(key not in seen, "Duplicate hypothesis structural context"); seen.add(key)
        if ref.get("residue") is not None:
            from .structures import RESIDUE_FIELDS
            fields(ref["residue"], {"source_key", "altloc"}, "hypothesis structural residue")
            fields(ref["residue"]["source_key"], RESIDUE_FIELDS, "hypothesis structural residue source key")
            json_value(ref["residue"]["source_key"], "structural residue source key")
            alt = ref["residue"]["altloc"]
            require(alt is None or isinstance(alt, str) and len(alt) <= 1, "Retain the actual alternate-location identifier or unknown null")


def validate_hypothesis_references(index, existing_entity_ids=frozenset()):
    for record in index.values():
        if record["type"] != "hypothesis":
            continue
        def resolve(key, kind):
            entity = index.get(key)
            require(entity is not None and entity["type"] == kind, "Unknown or wrong-type hypothesis " + kind)
            return entity
        molecules = {key: resolve(key, "molecule") for key in record["molecule_ids"]}
        for key in record["related_evidence_ids"]:
            evidence = resolve(key, "evidence")
            require(molecule_id_for(index[evidence["subject_id"]], index) in molecules,
                    "Hypothesis evidence belongs to a molecule outside its explicit scope")
        for key in record["lineage_ids"]:
            lineage = resolve(key, "lineage")
            require({lineage["parent_id"], lineage["child_id"]} <= molecules.keys(),
                    "Related lineage requires both parent and child in the hypothesis scope")
        for ref in record["residue_refs"]:
            require(ref["molecule_id"] in molecules, "Residue molecule is outside hypothesis scope")
            chain = next((c for c in molecules[ref["molecule_id"]]["chains"] if c["id"] == ref["chain_id"]), None)
            require(chain is not None and ref["sequence_index"] <= len(chain["sequence"]), "Hypothesis residue does not exist in the named molecule/chain")
        for ref in record["structure_refs"]:
            structure = resolve(ref["structure_id"], "structure")
            require(structure["molecule_id"] in molecules, "Structure molecule is outside hypothesis scope")
            from .structures import parse_structure
            models = parse_structure(structure["content"], structure["file_format"])["models"]
            require(ref["model"] in models, "Hypothesis source model does not exist; no invented model identity")
            if ref.get("residue") is not None:
                from .composition import exact_json
                from .structures import RESIDUE_FIELDS
                selected = ref["residue"]; key = selected["source_key"]
                require(exact_json(key["model"], ref["model"]), "Hypothesis residue and selected model differ")
                parsed = parse_structure(structure["content"], structure["file_format"])
                residue = next((r for r in parsed["residues"] if exact_json({field: r[field] for field in RESIDUE_FIELDS}, key)), None)
                require(residue is not None and selected["altloc"] in residue["altlocs"],
                        "Hypothesis source residue/conformer is absent from the named file/model; no neighbouring fallback")
            if ref["structure_map_id"] is not None:
                mapping = resolve(ref["structure_map_id"], "structure_map")
                require(mapping["structure_id"] == structure["id"], "Hypothesis correspondence belongs to another coordinate source")
                require(any(assignment["model"] == ref["model"] for assignment in mapping["chain_assignments"]),
                        "Hypothesis correspondence does not cover the selected source model")
                if record['id'] not in existing_entity_ids:
                    from .structures import correspondence_order
                    status, warning = correspondence_order(mapping, parse_structure(structure['content'], structure['file_format']))
                    require(status == 'verified', warning)


def hypothesis_preview(bundle, definition):
    fields(definition, {"text", "question", "limitations", "molecule_ids", "related_evidence_ids", "lineage_ids", "residue_refs", "structure_refs"}, "hypothesis definition")
    record = {**copy.deepcopy(definition), "id": new_id("hypothesis"), "type": "hypothesis", "project_id": bundle["project"]["id"],
              "created_at": now(), "status": "proposed", "source": {"name": "Antibody Insight local researcher entry", "version": __version__}}
    validate_extension(bundle["project"], bundle["entities"], [record])
    return {"schema_version": SCHEMA, "project": copy.deepcopy(bundle["project"]), "entities": [record]}
