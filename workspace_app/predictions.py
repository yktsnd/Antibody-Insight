"""F21/F22 P03/P08 J03/J08: original computed sources, never model execution.

Scalar native definitions: official AlphaFold3 docs/output.md, checked2026-11-04.
Pointers/allocations record import associations, not authenticated run identity.
"""

import copy
import hashlib
import json

from . import __version__
from .adapters import parse_json
from .domain import (MAX_SAFE_INTEGER, PREFIX, SCHEMA, ValidationError, fields, identifier, json_value,
                     new_id, now, number, require, source, text, timestamp, validate_entity,
                     validate_extension, validate_transport_size)
from .structures import parse_structure

CANONICAL = 'computed-evidence/1'
NATIVE = 'alphafold3-summary/1'
FORMATS = (CANONICAL, NATIVE)
SUBJECTS = ('molecule', 'construct', 'material', 'structure')
ROW_FIELDS = {'kind', 'subject_ref', 'metric', 'value', 'unit', 'source', 'timestamp', 'conditions'}
ROW_OPTIONAL = {'description', 'residue_refs'}
SCALARS = {'ptm': (0, 1), 'iptm': (0, 1), 'fraction_disordered': (0, 1), 'ranking_score': (-100, 1.5)}
MAX_SOURCE_BYTES = 24 * 1024 * 1024


def _exact(left, right):
    return json.dumps(left, sort_keys=True, ensure_ascii=False, allow_nan=False) == json.dumps(right, sort_keys=True, ensure_ascii=False, allow_nan=False)


def _pointer(path, key):
    return path + '/' + str(key).replace('~', '~0').replace('/', '~1')


def _app_kind(value):
    if not isinstance(value, str):
        return None
    for kind, prefix in PREFIX.items():
        if value.startswith(prefix+'_'):
            # An apparent application identifier is never redirected as an alias.
            identifier(value, kind)
            return kind
    return None


def _utf8(raw):
    require(isinstance(raw, str), 'Prediction JSON text required')
    try:
        encoded = raw.encode('utf-8')
    except UnicodeError as exc:
        raise ValidationError('Prediction source must be valid UTF-8 text') from exc
    require(0 < len(encoded) <= MAX_SOURCE_BYTES, 'Prediction source must contain 1–25,165,824 UTF-8 bytes; no truncation')
    return encoded


def validate_prediction_origin(evidence):
    require(evidence['kind'] == 'computed', 'Prediction origin is permitted only for computed Evidence')
    origin = evidence['prediction_origin']
    fields(origin, {'file_id', 'json_pointer'}, 'prediction_origin')
    identifier(origin['file_id'], 'prediction_file')
    text(origin['json_pointer'], 'Original source-value JSON pointer', 1000)


def validate_prediction_file_shape(record, *, pending=False):
    text(record['name'], 'Actual prediction file name', 500)
    require(record['file_format'] in FORMATS, 'Unsupported prediction JSON format')
    encoded = _utf8(record['content'])
    require(record['sha256'] == hashlib.sha256(encoded).hexdigest(), 'Prediction source content/hash mismatch')
    source(record['source'], 'Prediction importer')
    require(isinstance(record['bindings'], dict) and len(record['bindings']) <= 10000, 'Subject bindings must be an object of up to 10000 exact references')
    for ref, target in record['bindings'].items():
        text(ref, 'Original computed subject reference', 1000)
        require(_app_kind(ref) is None, 'Reserved application IDs cannot be remapped')
        require(_app_kind(target) in SUBJECTS, 'Choose an actual Molecule, Construct, Material or Structure ID')
    options = record['options']
    if record['file_format'] == CANONICAL:
        fields(options, set(), 'Canonical options')
    else:
        fields(options, {'structure_id', 'model', 'source', 'timestamp', 'conditions'}, 'Native summary options')
        identifier(options['structure_id'], 'structure')
        require(type(options['model']) is int and 1 <= options['model'] <= MAX_SAFE_INTEGER, 'Explicit actual positive coordinate-model ID required; no model1 default')
        source(options['source'], 'Original computation source')
        timestamp(options['timestamp'], 'Actual computation event time')
        require(options['conditions'] is None or isinstance(options['conditions'], dict), 'Computation conditions must be an object or null')
        json_value(options['conditions'], 'Computation conditions')
        require(not record['bindings'], 'Native structure/model binding uses explicit options, not external token mappings')
    allocations = record['allocations']
    require(isinstance(allocations, list) and (0 if pending else 1) <= len(allocations) <= 10000,
            'Prediction source requires 1–10000 actual scalar allocations before storage')
    pointers, ids = set(), set()
    for allocation in allocations:
        fields(allocation, {'json_pointer', 'evidence_id'}, 'Prediction allocation')
        text(allocation['json_pointer'], 'Allocated source pointer', 1000)
        identifier(allocation['evidence_id'], 'evidence')
        require(allocation['json_pointer'] not in pointers and allocation['evidence_id'] not in ids,
                'Duplicate prediction pointer or allocated Evidence ID')
        pointers.add(allocation['json_pointer']); ids.add(allocation['evidence_id'])


def _parse_file(raw, file_format):
    data = parse_json(raw.removeprefix('\ufeff'))
    try:
        json_value(data, 'Prediction source JSON')
    except RecursionError as exc:
        raise ValidationError('Prediction JSON nesting exceeds the supported limit') from exc
    require(isinstance(data, dict), 'Prediction JSON root must be an object')
    if file_format == NATIVE:
        require(any(key in data for key in SCALARS), 'No supported native summary scalar; arrays are not flattened into whole-structure values')
        for key, (low, high) in SCALARS.items():
            if key in data and data[key] is not None:
                number(data[key], 'Native '+key)
                require(low <= data[key] <= high, 'Native '+key+' outside its documented scalar range; entire summary rejected')
        return data, []
    unknown = [_pointer('', key) for key in data if key not in ('schema_version', 'records')]
    rows = data.get('records')
    if isinstance(rows, list):
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            path = '/records/'+str(i)
            unknown += [_pointer(path, key) for key in row if key not in ROW_FIELDS | ROW_OPTIONAL]
            if isinstance(row.get('source'), dict):
                unknown += [_pointer(path+'/source', key) for key in row['source'] if key not in ('name', 'version')]
            if isinstance(row.get('residue_refs'), list):
                for j, ref in enumerate(row['residue_refs']):
                    if isinstance(ref, dict):
                        unknown += [_pointer(path+'/residue_refs/'+str(j), key) for key in ref if key not in ('chain_id', 'sequence_index')]
    if unknown:
        raise ValidationError('Unsupported computed JSON fields; entire file rejected', sorted(unknown))
    require(data.get('schema_version') == CANONICAL, 'Expected computed-evidence/1 schema_version')
    require(isinstance(rows, list) and 1 <= len(rows) <= 10000, 'Canonical computed JSON requires 1–10000 records')
    return data, unknown


def _subject(ref, bindings, index, unresolved=None):
    text(ref, 'Original computed subject reference', 1000)
    kind = _app_kind(ref)
    if kind is not None:
        require(kind in SUBJECTS and ref in index and index[ref]['type'] == kind,
                'Reserved ID is not an available same-project computed subject; no remapping')
        return ref
    if ref not in bindings:
        if unresolved is not None:
            unresolved.add(ref)
        raise ValidationError('Unmapped external computed subject; explicitly choose the actual subject type and ID')
    target = bindings[ref]
    require(target in index and index[target]['type'] in SUBJECTS, 'Mapped computed subject is unavailable in this exact project')
    return target


def _base(record, pointer, values):
    return {'type': 'evidence', 'project_id': record['project_id'], 'created_at': record['created_at'],
            **copy.deepcopy(values), 'prediction_origin': {'file_id': record['id'], 'json_pointer': pointer}}


def _expected(record, index, unresolved=None):
    data, _ = _parse_file(record['content'], record['file_format'])
    expected, excluded = {}, []
    if record['file_format'] == NATIVE:
        options = record['options']; structure = index.get(options['structure_id'])
        require(structure is not None and structure['type'] == 'structure' and structure['origin_kind'] == 'computed',
                'Native summary requires an explicitly declared computed Structure')
        models = parse_structure(structure['content'], structure['file_format'])['models']
        require(options['model'] in models, 'Selected coordinate model does not exist in this exact Structure')
        conditions = copy.deepcopy(options['conditions']) if options['conditions'] is not None else {}
        require('structure_model' not in conditions or _exact(conditions['structure_model'], options['model']),
                'Supplied structure_model conflicts with the selected actual coordinate model')
        conditions['structure_model'] = options['model']
        for metric in SCALARS:
            if metric in data:
                pointer = _pointer('', metric)
                expected[pointer] = _base(record, pointer, {'subject_id': structure['id'], 'kind': 'computed',
                    'metric': metric, 'value': data[metric], 'unit': '1', 'source': options['source'],
                    'timestamp': options['timestamp'], 'conditions': conditions})
        return expected, excluded, sorted(_pointer('', key) for key in data if key not in SCALARS), data
    refs = {row.get('subject_ref') for row in data['records'] if isinstance(row, dict) and isinstance(row.get('subject_ref'), str)}
    require(set(record['bindings']) <= refs, 'Unused or stale computed subject binding key')
    for target in record['bindings'].values():
        require(target in index and index[target]['type'] in SUBJECTS, 'Mapped computed subject is unavailable in this exact project')
    for i, row in enumerate(data['records']):
        pointer = '/records/'+str(i)+'/value'
        try:
            fields(row, ROW_FIELDS, 'Computed record '+str(i+1), ROW_OPTIONAL)
            require(row['kind'] == 'computed', 'Computed adapter never converts a measured/literature/annotation row into a prediction')
            subject = _subject(row['subject_ref'], record['bindings'], index, unresolved)
            values = {key: copy.deepcopy(row[key]) for key in ('kind', 'metric', 'value', 'unit', 'source', 'timestamp', 'conditions')}
            values['subject_id'] = subject
            for key in ROW_OPTIONAL:
                if key in row:
                    values[key] = copy.deepcopy(row[key])
            entity = _base(record, pointer, values)
            validate_entity({**entity, 'id': new_id('evidence')}, record['project_id'])
            if entity.get('residue_refs'):
                from .domain import molecule_id_for
                from .residue_evidence import validate_evidence_position_references
                validate_evidence_position_references(entity, index[molecule_id_for(index[subject], index)])
            if index[subject]['type'] == 'structure' and entity['conditions'] is not None and 'structure_model' in entity['conditions']:
                model = entity['conditions']['structure_model']
                require(type(model) is int and model in parse_structure(index[subject]['content'], index[subject]['file_format'])['models'],
                        'Computed coordinate model is not an actual model of this exact Structure')
            expected[pointer] = entity
        except ValidationError as exc:
            excluded.append({'record_index': i+1, 'json_pointer': '/records/'+str(i), 'reason': str(exc), 'details': exc.details})
    return expected, excluded, [], data


def validate_prediction_references(index):
    sources = {e['id']: e for e in index.values() if e['type'] == 'prediction_file'}
    # Parse once per source/graph validation, not once per scalar or snapshot.
    parsed = {key: _expected(record, index)[0] for key, record in sources.items()}
    allocated = {}
    for key, record in sources.items():
        for allocation in record['allocations']:
            pointer, evidence_id = allocation['json_pointer'], allocation['evidence_id']
            require(pointer in parsed[key], 'Allocated prediction pointer is absent or refers to an excluded source record')
            evidence = index.get(evidence_id)
            require(evidence is not None and evidence['type'] == 'evidence', 'Allocated prediction Evidence dependency is missing')
            require(evidence.get('prediction_origin') == {'file_id': key, 'json_pointer': pointer}, 'Prediction allocation/origin mismatch')
            allocated[evidence_id] = (key, pointer)
    for evidence in index.values():
        if evidence['type'] != 'evidence' or 'prediction_origin' not in evidence:
            continue
        origin = evidence['prediction_origin']; key, pointer = origin['file_id'], origin['json_pointer']
        require(allocated.get(evidence['id']) == (key, pointer), 'Prediction Evidence is missing its exact retained source allocation')
        expected = parsed[key][pointer]
        actual = {field: value for field, value in evidence.items() if field not in ('id', 'created_at')}
        wanted = {field: value for field, value in expected.items() if field != 'created_at'}
        require(_exact(actual, wanted), 'Computed Evidence differs from its original source value/type/context/subject/scope')


def prediction_targets(bundle):
    result = []
    for record in bundle['entities']:
        if record['type'] == 'structure':
            models = parse_structure(record['content'], record['file_format'])['models']
            result.append({'id': record['id'], 'name': record['name'], 'sha256': record['sha256'], 'origin_kind': record['origin_kind'],
                           'models': [m for m in models if type(m) is int and m > 0], 'unknown_model_present': None in models})
    return {'structures': result}


def prediction_preview(bundle, raw, filename, file_format, bindings, options, bindings_text_sha256=None):
    encoded = _utf8(raw); digest = hashlib.sha256(encoded).hexdigest()
    require(file_format in FORMATS, 'Choose a supported computed JSON adapter explicitly')
    # The browser sends parameter JSON as text, preserving numeric types/signs.
    # Persisted source options still require an object/null, never this DTO form.
    options = copy.deepcopy(options)
    if file_format == NATIVE and isinstance(options, dict) and isinstance(options.get('conditions'), str):
        options['conditions'] = parse_json(options['conditions'])
    require(isinstance(bindings, dict), 'Computed subject bindings must be an object')
    require(not bindings or bindings_text_sha256 == digest, 'Stale computed binding: review this exact submitted UTF-8 text')
    record = {'id': new_id('prediction_file'), 'type': 'prediction_file', 'project_id': bundle['project']['id'], 'created_at': now(),
              'name': filename, 'file_format': file_format, 'content': raw, 'sha256': digest, 'bindings': copy.deepcopy(bindings),
              'options': copy.deepcopy(options), 'allocations': [],
              'source': {'name': 'Antibody Insight computed JSON importer', 'version': __version__}}
    # Validate a draft source before resolving rows. Actual stored records always
    # require nonempty allocations and are revalidated through the complete graph.
    validate_prediction_file_shape(record, pending=True)
    index = {e['id']: e for e in bundle['entities']}; unresolved = set()
    expected, excluded, unmapped, _ = _expected(record, index, unresolved)
    evidence = []
    for pointer, entity in expected.items():
        entity['id'] = new_id('evidence'); evidence.append(entity)
        record['allocations'].append({'json_pointer': pointer, 'evidence_id': entity['id']})
    incoming = [record, *evidence] if evidence else []
    validate_extension(bundle['project'], bundle['entities'], incoming)
    validate_transport_size(bundle['project'], [*bundle['entities'], *incoming])
    repeats = [e['id'] for e in bundle['entities'] if e['type'] == 'prediction_file' and e['sha256'] == digest]
    report = {'kind': 'computed_json', 'total_rows': len(expected)+len(excluded), 'valid_rows': len(evidence), 'excluded': excluded,
              'unresolved_refs': sorted(unresolved), 'unsupported_fields': unmapped, 'retained_unmapped_paths': unmapped,
              'text_utf8_sha256': digest, 'file_name': filename, 'bindings': copy.deepcopy(bindings), 'source_files_added': 1 if evidence else 0,
              'duplicates': [{'message': 'Potential repeated file content; no result identity or independent replicate is inferred', 'file_id': key} for key in repeats],
              'warnings': [{'message': 'Original JSON is retained once. Extracted scalars are computed results; coordinate-model/file association is a user assertion, not authenticated external sample identity.'}]}
    return {'bundle': {'schema_version': SCHEMA, 'project': copy.deepcopy(bundle['project']), 'entities': incoming}, 'report': report}
