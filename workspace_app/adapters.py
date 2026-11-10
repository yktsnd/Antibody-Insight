"""Explicit import contracts. No chain pairing, antibody numbering or predictions."""

from __future__ import annotations

import csv
import math
import hashlib
import io
import json
from decimal import Decimal

from .domain import AA, SCHEMA, ValidationError, fields, new_id, now, require, text, validate_entity, validate_project


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


def new_project(title, goal, data_class="research"):
    project = {"id": new_id("project"), "title": title, "goal": goal, "created_at": now(), "data_class": data_class}
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


def grouped_fasta_preview(raw, filename, project, options):
    """Explicit record-to-molecule/chain registration, never inferred pairing."""
    validate_project(project)
    fields(options, {'assignments', 'text_sha256', 'molecular_format'}, 'FASTA grouping options')
    rows = fasta_rows(raw)
    require(len(rows) <= 10000, 'Maximum 10,000 sequence records per import')
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    for row in rows:
        require(bool(row['external_id']) and bool(row['sequence']) and set(row['sequence']) <= AA,
                f"FASTA line {row['row']}: header and valid amino-acid sequence are required; no grouped records saved")
        require(len(row['sequence']) <= 100000, 'Sequence exceeds length limit')
    report = {'kind': 'grouped_fasta', 'total_rows': len(rows), 'valid_rows': 0,
              'excluded': [], 'duplicates': [], 'warnings': [], 'text_sha256': digest,
              'sequence_records': [{'record_index': i, **row} for i, row in enumerate(rows)]}
    result = {'bundle': {'schema_version': SCHEMA, 'project': project, 'entities': []}, 'report': report}
    if options['assignments'] is None: return result
    require(options['text_sha256'] == digest, 'FASTA text changed; review source records and assign chains again')
    text(options['molecular_format'], 'Declared molecular format', 500)
    assignments = options['assignments']
    require(isinstance(assignments, list) and len(assignments) == len(rows), 'Assign every source record explicitly')
    groups, used = {}, set()
    for assignment in assignments:
        fields(assignment, {'record_index', 'external_id', 'chain_id', 'role'}, 'FASTA chain assignment')
        position = assignment['record_index']
        require(type(position) is int and 0 <= position < len(rows) and position not in used, 'Duplicate or unknown FASTA record assignment')
        used.add(position)
        for key in ('external_id', 'chain_id', 'role'):
            text(assignment[key], 'Declared ' + key, 100 if key != 'external_id' else 500)
            require(assignment[key] == assignment[key].strip(), 'Remove surrounding whitespace from declared IDs/roles')
        external = assignment['external_id']
        group = groups.setdefault(external, {'chains': [], 'records': []})
        require(assignment['chain_id'] not in {c['id'] for c in group['chains']}, 'Duplicate chain ID within a declared candidate')
        group['chains'].append({'id': assignment['chain_id'], 'role': assignment['role'], 'sequence': rows[position]['sequence']})
        group['records'].append(f"record {position + 1}, line {rows[position]['row']}, header {rows[position]['external_id']}")
    for external, group in groups.items():
        entity = {'id': new_id('molecule'), 'type': 'molecule', 'project_id': project['id'], 'created_at': now(),
                  'external_id': external, 'name': external, 'format': options['molecular_format'], 'chains': group['chains'],
                  'source': {'name': filename + '; explicit FASTA grouping: ' + '; '.join(group['records']), 'version': 'sha256:' + digest}}
        validate_entity(entity, project['id'])
        result['bundle']['entities'].append(entity)
    report['valid_rows'] = len(rows)
    report['warnings'] = [{'message': 'Candidate/chain roles and molecular format are user declarations, not biological validation. Source record order is not a pairing rule.'}]
    report['sequence_records'] = []
    return result


def preview(raw, file_format, filename, project, structure_options=None, sequence_options=None):
    require(isinstance(raw, str), "File text required")
    require(isinstance(filename, str) and 0 < len(filename) <= 500, "Source filename required")
    if file_format == 'fasta_grouped':
        return grouped_fasta_preview(raw, filename, project, sequence_options)
    if file_format in ("pdb", "mmcif"):
        require(isinstance(structure_options, dict), "Import sequences first, then explicitly choose a structure's molecule")
        fields(structure_options, {"molecule_id", "origin_kind", "source_name", "source_version"}, "structure options")
        validate_project(project)
        entity = {"id": new_id("structure"), "type": "structure", "project_id": project["id"], "created_at": now(),
                  "name": filename, "molecule_id": structure_options["molecule_id"], "file_format": file_format, "content": raw,
                  "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(), "origin_kind": structure_options["origin_kind"],
                  "source": {"name": structure_options["source_name"] or filename, "version": structure_options["source_version"]}}
        validate_entity(entity, project["id"])
        return {"bundle": {"schema_version": SCHEMA, "project": project, "entities": [entity]},
                "report": {"total_rows": 1, "valid_rows": 1, "excluded": [], "duplicates": [],
                           "warnings": [{"message": "Coordinate source preserved. Chain/residue correspondence must be explicitly assigned; header/chemical metadata is retained but not automatically interpreted."}]}}
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
