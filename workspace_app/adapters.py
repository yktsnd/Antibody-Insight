"""Explicit import contracts. No chain pairing, antibody numbering or predictions."""

from __future__ import annotations

import csv
import math
import hashlib
import io
import json
from decimal import Decimal

from .domain import AA, SCHEMA, ValidationError, fields, new_id, now, require, validate_entity, validate_project


def parse_json(raw):
    def finite_float(token):
        value = float(token)
        require(math.isfinite(value), "JSON float exceeds finite range")
        require(value != 0.0 or Decimal(token) == 0, "Nonzero JSON float underflow; no data saved")
        return value

    def reject_constant(value):
        raise ValidationError(f"Non-finite JSON number rejected: {value}")

    def unique_keys(pairs):
        obj = {}
        for key, value in pairs:
            require(key not in obj, f"Duplicate JSON key: {key}")
            obj[key] = value
        return obj

    try:
        return json.loads(raw, parse_constant=reject_constant, parse_float=finite_float, object_pairs_hook=unique_keys)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValidationError("Invalid JSON file") from exc


def new_project(title, goal):
    project = {"id": new_id("project"), "title": title, "goal": goal, "created_at": now()}
    validate_project(project)
    return project


def fasta_rows(raw):
    rows = []
    header, seq, start = None, [], None
    for line_no, line in enumerate(raw.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                rows.append({"row": start, "external_id": header, "name": header, "sequence": "".join(seq)})
            header, seq, start = line[1:].strip(), [], line_no
        elif header is None:
            raise ValidationError(f"FASTA line {line_no}: sequence before header")
        else:
            seq.append("".join(line.split()).upper())
    if header is not None:
        rows.append({"row": start, "external_id": header, "name": header, "sequence": "".join(seq)})
    require(bool(rows), "No FASTA records found")
    return rows


def csv_rows(raw):
    try:
        reader = csv.DictReader(io.StringIO(raw), strict=True)
        headers = reader.fieldnames or []
        required = {"external_id", "name", "sequence"}
        allowed = required | {"chain_role", "format"}
        require(len(headers) == len(set(headers)), "Duplicate CSV headers")
        unknown = sorted(set(headers) - allowed)
        if unknown:
            raise ValidationError("Unsupported CSV fields; nothing was imported", unknown)
        require(required <= set(headers), "CSV requires external_id,name,sequence")
        rows = []
        for row in reader:
            require(None not in row, f"CSV line {reader.line_num}: too many columns")
            row["row"] = reader.line_num
            rows.append(row)
        require(bool(rows), "No CSV rows found")
        return rows
    except csv.Error as exc:
        raise ValidationError("Malformed CSV") from exc


def preview(raw, file_format, filename, project):
    require(isinstance(raw, str), "File text required")
    require(isinstance(filename, str) and 0 < len(filename) <= 500, "Source filename required")
    if file_format == "json":
        bundle = parse_json(raw)
        fields(bundle, {"schema_version", "project", "entities"}, "bundle")
        require(bundle["schema_version"] == SCHEMA, "Unsupported JSON schema; expected awx/1")
        # Full graph validation is done against the database before commit.
        validate_project(bundle["project"])
        require(isinstance(bundle["entities"], list) and len(bundle["entities"]) <= 50000, "Invalid entity list")
        for entity in bundle["entities"]:
            validate_entity(entity, bundle["project"]["id"])
        return {"bundle": bundle, "report": {"total_rows": len(bundle["entities"]),
                "valid_rows": len(bundle["entities"]), "excluded": [], "warnings": [], "duplicates": []}}
    require(file_format in ("fasta", "csv"), "Unsupported file format; PDB/mmCIF and prediction adapters are not implemented")
    validate_project(project)
    rows = fasta_rows(raw) if file_format == "fasta" else csv_rows(raw)
    require(len(rows) <= 10000, "Maximum 10,000 sequence records per import")
    report = {"total_rows": len(rows), "valid_rows": 0, "excluded": [], "warnings": [], "duplicates": []}
    entities, seen_ids, seen_sequences = [], set(), {}
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    for row in rows:
        external = (row.get("external_id") or "").strip()
        name = (row.get("name") or "").strip()
        seq = "".join((row.get("sequence") or "").split()).upper()
        reason = None
        if not external or not name:
            reason = "Missing external ID or name"
        elif external in seen_ids:
            reason = "Duplicate external ID in input"
        elif not seq:
            reason = "Missing sequence"
        elif not set(seq) <= AA:
            reason = "Invalid amino-acid symbols"
        elif len(seq) > 100000 or len(external) > 500 or len(name) > 500:
            reason = "Record exceeds length limit"
        if reason:
            report["excluded"].append({"row": row["row"], "external_id": external, "reason": reason})
            continue
        seen_ids.add(external)
        if seq in seen_sequences:
            report["duplicates"].append({"external_id": external, "same_sequence_as": seen_sequences[seq]})
        else:
            seen_sequences[seq] = external
        unusual = sorted(set(seq) & set("BXZJUO"))
        if unusual:
            report["warnings"].append({"external_id": external, "message": "Ambiguous or non-standard symbols: " + "".join(unusual)})
        entity = {"id": new_id("molecule"), "type": "molecule", "project_id": project["id"],
                  "created_at": now(), "external_id": external, "name": name,
                  "format": (row.get("format") or "unspecified").strip(),
                  "chains": [{"id": "chain-1", "role": (row.get("chain_role") or "unknown").strip(), "sequence": seq}],
                  "source": {"name": filename, "version": "sha256:" + digest}}
        validate_entity(entity, project["id"])
        entities.append(entity)
    report["valid_rows"] = len(entities)
    return {"bundle": {"schema_version": SCHEMA, "project": project, "entities": entities}, "report": report}
