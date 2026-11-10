"""F16, P06/P08, J06/J08: explicit measured-row source and Material association."""

import copy
import csv
import hashlib
import io
import json
import re
from decimal import Decimal, InvalidOperation

from . import __version__
from .adapters import parse_json
from .domain import (MAX_SAFE_INTEGER, PREFIX, SCHEMA, ValidationError, fields, identifier,
                     new_id, now, number, require, source, text, validate_entity, validate_extension)


def validate_import_origin(origin):
    fields(origin, {'file_name', 'text_utf8_sha256', 'record_index', 'line_number', 'source_material_ref', 'importer'}, 'import_origin')
    text(origin['file_name'], 'Imported file name', 500)
    text(origin['source_material_ref'], 'Original Material reference', 1000)
    require(isinstance(origin['text_utf8_sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', origin['text_utf8_sha256']) is not None,
            'Import text digest must be a lowercase SHA-256 value; it is recorded provenance, not authenticated file verification')
    for key in ('record_index', 'line_number'):
        require(type(origin[key]) is int and 1 <= origin[key] <= MAX_SAFE_INTEGER, 'Import row/line must be a positive safe integer')
    require(origin['line_number'] >= origin['record_index'] + 1, 'CSV end-line cannot precede its logical data record after the header')
    source(origin['importer'], 'import_origin.importer')


def _canonical_kind(value):
    for kind, prefix in PREFIX.items():
        if value.startswith(prefix + '_'):
            try:
                identifier(value, kind)
                return kind
            except ValidationError:
                return None
    return None


def _scalar(token):
    if token == '':
        return None
    require(re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', token) is not None,
            'Expected a decimal-point numeric value or empty/null; qualifiers such as ND and <0.1 are not point values')
    # Bound before int conversion; a huge exponent must never allocate a huge integer.
    require(len(token) <= 1000, 'Numeric token exceeds length limit')
    try:
        exact = Decimal(token)
        value = float(exact)
    except (InvalidOperation, OverflowError, ValueError) as exc:
        raise ValidationError('Measured number is outside the supported finite range') from exc
    number(value, 'Measured value')
    require(value != 0.0 or exact == 0, 'Nonzero measured value underflow; no zero substitution')
    if re.fullmatch(r'[+-]?[0-9]+', token):
        value = int(token)
        number(value, 'Measured value')
    return value


def _repeat_key(entity):
    return json.dumps({key: entity[key] for key in ('subject_id', 'kind', 'metric', 'timestamp', 'conditions', 'value', 'unit', 'source')},
                      sort_keys=True, ensure_ascii=False, allow_nan=False)


def measurement_preview(bundle, raw, filename, mappings=None, file_source=None, mapping_text_sha256=None):
    """Preview only. Actual measured rows always name a same-project Material ID."""
    require(isinstance(raw, str), 'CSV text required')
    text(filename, 'Actual input file name', 500)
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    mappings = {} if mappings is None else mappings
    require(isinstance(mappings, dict), 'Material mappings must be an object')
    if mappings:
        require(mapping_text_sha256 == digest, 'Stale file mapping: review mappings for this exact submitted UTF-8 text')
    supplied_source = {'name': filename, 'version': None} if file_source is None else file_source
    source(supplied_source, 'File source')
    required = {'material_ref', 'metric', 'value', 'unit', 'timestamp'}
    optional = {'conditions_json', 'description', 'source_name', 'source_version'}
    try:
        reader = csv.DictReader(io.StringIO(raw.removeprefix('\ufeff'), newline=''), strict=True)
        headers = reader.fieldnames or []
        require(len(headers) == len(set(headers)), 'Duplicate measurement CSV headers')
        unknown = sorted(set(headers) - required - optional)
        if unknown:
            raise ValidationError('Unsupported measurement CSV fields; nothing was imported', unknown)
        require(required <= set(headers), 'Measurement CSV requires material_ref,metric,value,unit,timestamp')
        row_source = 'source_name' in headers
        require(row_source == ('source_version' in headers), 'source_name and source_version headers must be supplied together')
        rows = []
        for record_index, row in enumerate(reader, 1):
            require(record_index <= 10000, 'Maximum 10,000 measurement records per import')
            rows.append((record_index, reader.line_num, row))
    except csv.Error as exc:
        raise ValidationError('Malformed measurement CSV; no data saved') from exc
    require(bool(rows), 'No measurement records found')
    index = {e['id']: e for e in bundle['entities']}
    material_ids = {e['id'] for e in bundle['entities'] if e['type'] == 'material'}
    refs = {row.get('material_ref') for _, _, row in rows}
    for ref, target in mappings.items():
        text(ref, 'Mapped original Material reference', 1000)
        require(ref in refs, 'Unused or stale Material mapping key')
        require(_canonical_kind(ref) is None, 'Canonical application IDs are reserved and cannot be remapped')
        identifier(target, 'material')
        require(target in material_ids, 'Mapped Material is unavailable in this exact project')
    report = {'kind': 'measurement_csv', 'total_rows': len(rows), 'valid_rows': 0, 'excluded': [], 'warnings': [],
              'duplicates': [], 'unresolved_refs': [], 'text_utf8_sha256': digest, 'file_name': filename,
              'source_mode': 'per_row' if row_source else 'file', 'file_source': copy.deepcopy(supplied_source),
              'mappings': copy.deepcopy(mappings), 'unsupported_fields': []}
    entities, unresolved = [], set()
    seen = {}
    for existing in index.values():
        if existing['type'] == 'evidence':
            seen.setdefault(_repeat_key(existing), existing['id'])
    for record_index, line_number, row in rows:
        ref = row.get('material_ref')
        try:
            require(None not in row and all(value is not None for value in row.values()), 'CSV column count does not match header')
            text(ref, 'Original Material reference', 1000)
            kind = _canonical_kind(ref)
            if kind is not None:
                require(kind == 'material' and ref in material_ids, 'Canonical ID is not an available same-project Material; it cannot be remapped')
                target = ref
            else:
                if ref not in mappings:
                    unresolved.add(ref)
                    raise ValidationError('Unmapped external Material reference; choose an actual Material explicitly')
                target = mappings[ref]
            conditions_raw = row.get('conditions_json', '')
            conditions = parse_json(conditions_raw) if conditions_raw else None
            require(conditions is None or isinstance(conditions, dict), 'Measurement conditions must be a JSON object or null')
            actual_source = {'name': row['source_name'], 'version': row['source_version'] or None} if row_source else copy.deepcopy(supplied_source)
            entity = {'id': new_id('evidence'), 'type': 'evidence', 'project_id': bundle['project']['id'], 'created_at': now(),
                      'subject_id': target, 'kind': 'measured', 'metric': row['metric'], 'value': _scalar(row['value']),
                      'unit': row['unit'] or None, 'timestamp': row['timestamp'], 'conditions': conditions, 'source': actual_source,
                      'import_origin': {'file_name': filename, 'text_utf8_sha256': digest, 'record_index': record_index,
                                        'line_number': line_number, 'source_material_ref': ref,
                                        'importer': {'name': 'Antibody Insight measurement CSV importer', 'version': __version__}}}
            if row.get('description'):
                entity['description'] = row['description']
            validate_entity(entity, bundle['project']['id'])
            key = _repeat_key(entity)
            if key in seen:
                report['duplicates'].append({'record_index': record_index, 'row': line_number, 'same_values_as_evidence_id': seen[key],
                                             'message': 'Potential repeated source observation; retained as a separate record. Independence is not established.'})
            seen.setdefault(key, entity['id'])
            entities.append(entity)
        except ValidationError as exc:
            report['excluded'].append({'record_index': record_index, 'row': line_number, 'material_ref': ref,
                                       'reason': str(exc), 'details': exc.details})
    validate_extension(bundle['project'], bundle['entities'], entities)
    report['valid_rows'] = len(entities)
    report['unresolved_refs'] = sorted(unresolved)
    return {'bundle': {'schema_version': SCHEMA, 'project': copy.deepcopy(bundle['project']), 'entities': entities}, 'report': report}
