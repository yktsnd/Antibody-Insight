"""F17/F18, P06/J06: declared construct/material identity and original observations."""

import copy

from . import __version__
from .domain import SCHEMA, fields, identifier, new_id, now, require, validate_extension
from .observation import context_issue, context_key


def metadata_preview(bundle, definition):
    require(isinstance(definition, dict), 'Metadata definition must be an object')
    kind = definition.get('type')
    require(kind in ('construct', 'material'), 'Choose an explicit Construct or Material record')
    expected = {'type', 'name', 'molecule_id', 'cds', 'vector', 'signal_peptide'} if kind == 'construct' else {'type', 'name', 'construct_id', 'lot'}
    fields(definition, expected, 'metadata definition')
    record = {**copy.deepcopy(definition), 'id': new_id(kind), 'project_id': bundle['project']['id'], 'created_at': now(),
              'source': {'name': 'Antibody Insight local researcher metadata entry', 'version': __version__}}
    validate_extension(bundle['project'], bundle['entities'], [record])
    return {'schema_version': SCHEMA, 'project': copy.deepcopy(bundle['project']), 'entities': [record]}


def _recorded_field(left, right):
    return {'left': left, 'right': right, 'status': 'unavailable' if left is None or right is None else
            'same_recorded_value' if left == right else 'different_recorded_values'}


def construct_context(bundle, molecule_id, left_id=None, right_id=None, cohort_id=None):
    identifier(molecule_id, 'molecule'); index = {e['id']: e for e in bundle['entities']}
    molecule = index.get(molecule_id)
    require(molecule is not None and molecule['type'] == 'molecule', 'Unknown or wrong-type Molecule context')
    constructs = [e for e in bundle['entities'] if e['type'] == 'construct' and e['molecule_id'] == molecule_id]
    available = {e['id']: e for e in constructs}
    for key in (left_id, right_id):
        if key is not None:
            identifier(key, 'construct')
            require(key in available, 'Construct is unavailable in this exact Molecule context; equal sequence is not identity')
    require(left_id is None or right_id is None or left_id != right_id, 'Choose two distinct actual Construct IDs')
    selected = {key for key in (left_id, right_id) if key is not None}
    material_ids = {e['id'] for e in bundle['entities'] if e['type'] == 'material' and e['construct_id'] in (selected or available.keys())}
    materials = [e for e in bundle['entities'] if e['id'] in material_ids]
    # A Molecule- or Construct-level result is never repeated as each Material's observation.
    observations = [e for e in bundle['entities'] if e['type'] == 'evidence' and e['subject_id'] in material_ids]
    groups, eligible, excluded = {}, {}, []
    for evidence in sorted(observations, key=lambda e: e['id']):
        issue = context_issue(evidence)
        if issue:
            excluded.append({'evidence_id': evidence['id'], 'reason': issue})
            continue
        key = context_key(evidence); eligible[evidence['id']] = key
        if key not in groups:
            groups[key] = {'id': evidence['id'], 'evidence_ids': [], 'kind': evidence['kind'], 'metric': evidence['metric'],
                           'unit': evidence['unit'], 'conditions': copy.deepcopy(evidence['conditions']), 'source': copy.deepcopy(evidence['source'])}
        groups[key]['evidence_ids'].append(evidence['id'])
    require(cohort_id is None or isinstance(cohort_id, str) and cohort_id in eligible,
            'Chosen observation context is unavailable or incomplete for these actual Constructs/Materials')
    selected_key = eligible.get(cohort_id)
    comparison = None
    if left_id is not None and right_id is not None:
        left, right = available[left_id], available[right_id]
        comparison = {key: _recorded_field(left[key], right[key]) for key in ('cds', 'vector', 'signal_peptide')}
        cds = comparison['cds']
        cds['left_length'] = len(left['cds']) if left['cds'] is not None else None
        cds['right_length'] = len(right['cds']) if right['cds'] is not None else None
        cds['raw_differences'] = []
        if cds['status'] != 'unavailable':
            for position in range(max(cds['left_length'], cds['right_length'])):
                a = left['cds'][position] if position < cds['left_length'] else None
                b = right['cds'][position] if position < cds['right_length'] else None
                if a != b:
                    cds['raw_differences'].append({'raw_dna_index': position + 1, 'left': a, 'right': b})
    return {'molecule': copy.deepcopy(molecule), 'constructs': copy.deepcopy(constructs), 'materials': copy.deepcopy(materials),
            'left_id': left_id, 'right_id': right_id, 'comparison': comparison,
            'observations': copy.deepcopy(observations), 'cohorts': list(groups.values()), 'ineligible': excluded,
            'cohort_id': cohort_id,
            'context_evidence_ids': [e['id'] for e in observations if selected_key is not None and eligible.get(e['id']) == selected_key]}
