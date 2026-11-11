"""Identity and provenance invariants. P01/P06/P07/P08, J01/J06/J07/J08."""

from __future__ import annotations

import copy
import json
import math
import uuid
from datetime import datetime, timezone

SCHEMA = "awx/1"
PREFIX = {"project": "prj", "molecule": "mol", "construct": "con", "material": "mat",
          "evidence": "evd", "decision": "dec", "binding_unit": "bnd", "lineage": "lin", "residue_map": "rmp",
          "structure": "stc", "structure_map": "smp", "hypothesis": "hyp", "prediction_file": "prf",
          "numbering_file": "nmf"}
AA = frozenset("ACDEFGHIKLMNPQRSTVWYBXZJUO")
MAX_SAFE_INTEGER = 2**53 - 1
MAX_BUNDLE_BYTES = 32 * 1024 * 1024
CORE = {"id", "type", "project_id", "created_at"}
FIELDS = {
    "molecule": {"name", "external_id", "format", "chains", "source"},
    "construct": {"name", "molecule_id", "cds", "vector", "signal_peptide"},
    "material": {"name", "construct_id", "lot"},
    "binding_unit": {"name", "topology", "chains", "source"},
    "lineage": {"parent_id", "child_id", "change_set"},
    "residue_map": {"molecule_id", "chain_id", "domain_id", "chain_type", "scheme", "definition", "status", "reason",
                    "sequence_start", "sequence_end", "source", "verification", "entries"},
    "structure": {"name", "molecule_id", "file_format", "content", "sha256", "origin_kind", "source"},
    "structure_map": {"structure_id", "molecule_id", "source", "chain_assignments", "residues"},
    "prediction_file": {"name", "file_format", "content", "sha256", "bindings", "options", "allocations", "source"},
    "numbering_file": {"name", "file_format", "content", "sha256", "allocations", "source"},
    "evidence": {"subject_id", "kind", "metric", "source", "timestamp", "conditions", "value", "unit"},
    "hypothesis": {"text", "question", "limitations", "molecule_ids", "related_evidence_ids", "lineage_ids", "residue_refs", "structure_refs", "status", "source"},
    "decision": {"candidate_ids", "criteria", "evidence_snapshot", "reason", "timestamp",
                 "revision", "supersedes", "status"},
}


class ValidationError(ValueError):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details or []


def now():
    return datetime.now(timezone.utc).isoformat()


def new_id(kind):
    return f"{PREFIX[kind]}_{uuid.uuid4()}"


def require(test, message):
    if not test:
        raise ValidationError(message)


def fields(obj, required, path, optional=frozenset()):
    require(isinstance(obj, dict), f"{path}: expected object")
    unknown = sorted(set(obj) - required - optional)
    missing = sorted(required - set(obj))
    if unknown:
        raise ValidationError("Unsupported fields; nothing was imported", [f"{path}.{x}" for x in unknown])
    require(not missing, f"{path}: missing fields {', '.join(missing)}")


def text(value, path, limit=10000):
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= limit,
            f"{path}: non-empty text required (max {limit})")
    require(not any(ord(c) < 32 and c not in "\n\r\t" for c in value), f"{path}: control character")


def nullable_text(value, path):
    if value is not None:
        text(value, path)


def identifier(value, kind):
    require(isinstance(value, str), f"{kind} ID must be text")
    prefix = PREFIX[kind] + "_"
    require(value.startswith(prefix), f"Expected {prefix}UUID identifier")
    try:
        parsed = uuid.UUID(value[len(prefix):])
    except ValueError as exc:
        raise ValidationError(f"Invalid {kind} UUID") from exc
    require(str(parsed) == value[len(prefix):], f"Non-canonical {kind} UUID")


def timestamp(value, path):
    require(isinstance(value, str), f"{path}: timestamp required")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{path}: invalid ISO 8601 timestamp") from exc
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None, f"{path}: timezone required")


def source(value, path):
    fields(value, {"name", "version"}, path)
    text(value["name"], path + ".name")
    nullable_text(value["version"], path + ".version")


def sequence(value, path):
    text(value, path, 100000)
    require(set(value) <= AA, f"{path}: invalid amino-acid symbols")


def number(value, path):
    require(type(value) in (int, float), f"{path}: numerical value required")
    if type(value) is int:
        require(abs(value) <= MAX_SAFE_INTEGER, f"{path}: integer exceeds interoperable JSON range")
    else:
        require(math.isfinite(value), f"{path}: non-finite number")
        require(not value.is_integer() or abs(value) <= MAX_SAFE_INTEGER,
                f"{path}: integer exceeds interoperable JSON range")


def validate_transport_size(project, entities):
    """Every accepted project must fit its actual complete UTF-8 import wrapper."""
    try:
        size = len(json.dumps({'schema_version': SCHEMA, 'project': project, 'entities': entities},
                              ensure_ascii=False, allow_nan=False).encode('utf-8'))
    except (UnicodeError, ValueError, TypeError) as exc:
        raise ValidationError('Project must be valid finite UTF-8 JSON for export/reimport') from exc
    require(size <= MAX_BUNDLE_BYTES,
            'Complete JSON-escaped project exceeds the 32 MiB export/reimport request limit; no data saved or truncated')
    return size


def json_value(value, path):
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, (int, float)):
        number(value, path)
    elif isinstance(value, list):
        for v in value:
            json_value(v, path)
    elif isinstance(value, dict):
        for k, v in value.items():
            require(isinstance(k, str), f"{path}: text keys required")
            json_value(v, path + "." + k)
    else:
        raise ValidationError(f"{path}: invalid JSON value")


def molecule_id_for(entity, index):
    """Resolve a subject without inferring ownership from equal sequences."""
    if entity["type"] == "molecule":
        return entity["id"]
    if entity["type"] == "construct":
        return entity["molecule_id"]
    if entity["type"] == "structure":
        return entity["molecule_id"]
    if entity["type"] == "material":
        construct = index.get(entity["construct_id"])
        require(construct is not None and construct["type"] == "construct",
                f"Unknown construct reference: {entity['construct_id']}")
        return construct["molecule_id"]
    return None


def validate_project(project):
    fields(project, {"id", "title", "goal", "created_at"}, "project", {"data_class"})
    identifier(project["id"], "project")
    text(project["title"], "project.title", 200)
    text(project["goal"], "project.goal")
    timestamp(project["created_at"], "project.created_at")
    require(project.get("data_class", "research") in ("research", "synthetic_fixture"), "Unsupported project data class")


def validate_entity(entity, project_id):
    require(isinstance(entity, dict), "entity must be object")
    kind = entity.get("type")
    require(isinstance(kind, str) and kind in FIELDS, "Unsupported entity type")
    optional = ({"component_graph"} if kind == "molecule" else {"residue_refs", "description", "import_origin", "prediction_origin"} if kind == "evidence"
                else {"derivation"} if kind == "structure_map"
                else {"numbering_origin"} if kind == "residue_map"
                else {"source"} if kind in ("construct", "material") else {"chosen_candidate_ids", "source", "hypothesis_ids"} if kind == "decision" else frozenset())
    fields(entity, CORE | FIELDS[kind], "entity", optional)
    identifier(entity["id"], kind)
    require(entity["project_id"] == project_id, "Cross-project entity rejected")
    timestamp(entity["created_at"], "created_at")
    if kind == "molecule":
        for key in ("name", "external_id", "format"):
            text(entity[key], key, 500)
        source(entity["source"], "source")
        chains = entity["chains"]
        require(isinstance(chains, list) and 0 < len(chains) <= 100, "Non-empty chain list required")
        seen = set()
        for chain in chains:
            fields(chain, {"id", "role", "sequence"}, "chain")
            text(chain["id"], "chain.id", 100)
            require(chain["id"] not in seen, "Duplicate chain ID within molecule")
            seen.add(chain["id"])
            text(chain["role"], "chain.role", 100)
            sequence(chain["sequence"], "chain.sequence")
        from .composition import validate_component_graph_shape
        validate_component_graph_shape(entity)
    elif kind in ("binding_unit", "lineage"):
        from .composition import validate_composition_entity
        validate_composition_entity(entity)
    elif kind == "residue_map":
        from .numbering import validate_numbering_shape
        validate_numbering_shape(entity)
    elif kind == "numbering_file":
        from .numbering_import import validate_numbering_file
        validate_numbering_file(entity)
    elif kind in ("structure", "structure_map"):
        from .structures import validate_structure_shape
        validate_structure_shape(entity)
    elif kind == "hypothesis":
        from .hypotheses import validate_hypothesis_shape
        validate_hypothesis_shape(entity)
    elif kind == "construct":
        text(entity["name"], "construct.name")
        identifier(entity["molecule_id"], "molecule")
        for key in ("cds", "vector", "signal_peptide"):
            nullable_text(entity[key], key)
        if entity["cds"] is not None:
            require(set(entity["cds"]) <= set("ACGTN"), "CDS must use uppercase ACGTN; translation not validated")
        if "source" in entity:
            source(entity["source"], "construct.source")
    elif kind == "material":
        text(entity["name"], "material.name")
        identifier(entity["construct_id"], "construct")
        text(entity["lot"], "material.lot")
        if "source" in entity:
            source(entity["source"], "material.source")
    elif kind == "prediction_file":
        from .predictions import validate_prediction_file_shape
        validate_prediction_file_shape(entity)
    elif kind == "evidence":
        text(entity["subject_id"], "evidence.subject_id")
        require(entity["kind"] in ("measured", "computed", "literature", "annotation"), "Invalid evidence kind")
        text(entity["metric"], "evidence.metric")
        source(entity["source"], "evidence.source")
        timestamp(entity["timestamp"], "evidence.timestamp")
        require(entity["conditions"] is None or isinstance(entity["conditions"], dict), "conditions must be object or null")
        json_value(entity["conditions"], "conditions")
        value = entity["value"]
        if value is not None:
            number(value, "value")
        nullable_text(entity["unit"], "unit")
        require(value is None or entity["unit"] is not None, "Numerical values require a unit; use 1 for dimensionless")
        nullable_text(entity.get("description"), "Evidence description")
        from .residue_evidence import validate_evidence_position_shape
        validate_evidence_position_shape(entity.get("residue_refs", []))
        if "import_origin" in entity:
            from .measurements import validate_import_origin
            validate_import_origin(entity["import_origin"])
        if "prediction_origin" in entity:
            from .predictions import validate_prediction_origin
            validate_prediction_origin(entity)
        from .structures import validate_model_metric
        validate_model_metric(entity)
    elif kind == "decision":
        from .decisions import validate_decision_shape
        validate_decision_shape(entity)
        text(entity["reason"], "decision.reason")
        timestamp(entity["timestamp"], "decision.timestamp")
        candidates = entity["candidate_ids"]
        require(isinstance(candidates, list) and 0 < len(candidates) <= 1000, "Select 1–1000 candidates")
        for candidate in candidates:
            identifier(candidate, "molecule")
        require(len(set(candidates)) == len(candidates), "Duplicate candidate IDs")
        require(isinstance(entity["evidence_snapshot"], list), "Evidence snapshot must be list")


def validate_extension(project, previous, incoming):
    """Validate an append against trusted stored records, never caller exemptions.

    Legacy maps retain all identity/reference checks. Their source-order status
    is checked when observed; newly supplied maps and hypotheses are checked now.
    """
    return validate_graph(project, [*previous, *incoming], existing_entity_ids={e['id'] for e in previous})


def validate_graph(project, entities, *, existing_entity_ids=frozenset()):
    validate_project(project)
    require(isinstance(entities, list) and len(entities) <= 50000, "Entity list too large or invalid")
    index = {}
    external_ids = set()
    for entity in entities:
        validate_entity(entity, project["id"])
        require(entity["id"] not in index, "Duplicate internal ID; no overwrite")
        index[entity["id"]] = entity
        if entity["type"] == "molecule":
            ext = entity["external_id"]
            require(ext not in external_ids, f"External ID collision: {ext}")
            external_ids.add(ext)

    def ref(key, expected):
        require(isinstance(key, str) and key in index, f"Unknown reference: {key}")
        target = index[key]
        require(target["type"] in expected, f"Wrong reference type: {key}")
        return target

    for entity in entities:
        kind = entity["type"]
        if kind == "construct":
            ref(entity["molecule_id"], {"molecule"})
        elif kind == "material":
            ref(entity["construct_id"], {"construct"})
        elif kind == "evidence":
            subject = ref(entity["subject_id"], {"molecule", "construct", "material", "structure"})
            require(entity["kind"] != "measured" or subject["type"] == "material",
                    "Measured evidence requires an explicit Material ID")
            if entity.get("residue_refs"):
                from .residue_evidence import validate_evidence_position_references
                molecule = ref(molecule_id_for(subject, index), {"molecule"})
                validate_evidence_position_references(entity, molecule)
        elif kind == "decision":
            for key in entity["candidate_ids"]:
                ref(key, {"molecule"})
            snapshot_ids = set()
            for snapshot in entity["evidence_snapshot"]:
                require(isinstance(snapshot, dict), "Snapshot must contain complete Evidence objects")
                original = ref(snapshot.get("id"), {"evidence"})
                validate_entity(snapshot, project["id"])
                require(json.dumps(snapshot, sort_keys=True, allow_nan=False) ==
                        json.dumps(original, sort_keys=True, allow_nan=False),
                        "Evidence snapshot differs from stored source")
                require(original["id"] not in snapshot_ids, "Duplicate snapshot evidence")
                snapshot_ids.add(original["id"])
                subject = ref(original["subject_id"], {"molecule", "construct", "material", "structure"})
                require(molecule_id_for(subject, index) in entity["candidate_ids"],
                        "Evidence does not belong to selected candidates")
    from .composition import validate_composition_references
    validate_composition_references(index, project)
    from .numbering import validate_numbering_references
    validate_numbering_references(project, index)
    from .numbering_import import validate_numbering_origins
    validate_numbering_origins(index)
    from .structures import validate_structure_references
    validate_structure_references(index, existing_entity_ids)
    from .hypotheses import validate_hypothesis_references
    validate_hypothesis_references(index, existing_entity_ids)
    from .decisions import validate_decision_references
    validate_decision_references(index)
    from .predictions import validate_prediction_references
    validate_prediction_references(index)
    return index


def shortlist(project, entities, candidate_ids, evidence_ids, reason):
    """Immutable draft, not an acceptance of incomplete scientific criteria."""
    index = validate_extension(project, entities, [])
    require(isinstance(evidence_ids, list) and all(isinstance(x, str) for x in evidence_ids), "Evidence IDs must be list of text")
    require(len(set(evidence_ids)) == len(evidence_ids), "Duplicate evidence IDs")
    require(all(x in index and index[x]["type"] == "evidence" for x in evidence_ids), "Unknown evidence ID")
    created = now()
    decision = {"id": new_id("decision"), "type": "decision", "project_id": project["id"],
                "created_at": created, "timestamp": created, "candidate_ids": candidate_ids,
                "criteria": [], "evidence_snapshot": [copy.deepcopy(index[x]) for x in evidence_ids],
                "reason": reason, "revision": 1, "supersedes": None, "status": "draft"}
    validate_extension(project, entities, [decision])
    return decision
