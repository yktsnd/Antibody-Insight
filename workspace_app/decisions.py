"""F19/F20 P07/P08 J07/J08: explicit observations and immutable human decisions.

Weights/preferences are researcher declarations. No ranking, normalized score,
biological comparability or recommendation is inferred.
"""

import copy
import json

from . import __version__
from .adapters import parse_json
from .domain import (MAX_SAFE_INTEGER, SCHEMA, ValidationError, fields, identifier, molecule_id_for,
                     new_id, now, number, require, source, text, validate_extension)
from .hypotheses import id_list
from .observation import context_issue, context_key

NEW_FIELDS = {'chosen_candidate_ids', 'source', 'hypothesis_ids'}
CRITERION_FIELDS = {'key', 'name', 'weight', 'required', 'preference', 'anchor_evidence_id', 'evidence_choices'}


def is_legacy(record):
    return not NEW_FIELDS.intersection(record)


def validate_decision_shape(record):
    if is_legacy(record):
        require(record['criteria'] == [] and record['status'] == 'draft', 'Legacy shortlist must be an empty-criteria draft')
        require(type(record['revision']) is int and record['revision'] == 1 and record['supersedes'] is None,
                'Legacy draft revision must be 1 without supersedes')
        return
    require(NEW_FIELDS <= record.keys(), 'New Decision requires chosen_candidate_ids, source and hypothesis_ids together')
    id_list(record['candidate_ids'], 'molecule', 'Comparison candidates', nonempty=True)
    require(record['status'] in ('draft', 'finalized'), 'Decision status must be draft or finalized')
    require(type(record['revision']) is int and 1 <= record['revision'] <= MAX_SAFE_INTEGER, 'Decision revision must be a positive safe integer')
    if record['supersedes'] is None:
        require(record['revision'] == 1, 'First Decision version must have revision 1')
    else:
        identifier(record['supersedes'], 'decision')
        require(record['revision'] > 1, 'A successor Decision must increment its predecessor revision')
    id_list(record['chosen_candidate_ids'], 'molecule', 'Chosen candidates')
    id_list(record['hypothesis_ids'], 'hypothesis', 'Supporting hypotheses')
    require(set(record['chosen_candidate_ids']) <= set(record['candidate_ids']), 'Chosen IDs must belong to the actual comparison scope')
    source(record['source'], 'Decision entry source')
    require(isinstance(record['criteria'], list) and len(record['criteria']) <= 20, 'Decision supports up to 20 explicit criteria')
    keys = set()
    for criterion in record['criteria']:
        fields(criterion, CRITERION_FIELDS, 'Decision criterion')
        text(criterion['key'], 'Criterion key', 100)
        text(criterion['name'], 'Criterion name', 200)
        require(criterion['key'] not in keys, 'Duplicate criterion key')
        keys.add(criterion['key'])
        number(criterion['weight'], 'Declared criterion weight')
        require(criterion['weight'] >= 0, 'Declared criterion weight cannot be negative')
        require(type(criterion['required']) is bool, 'Required flag must be a boolean')
        require(criterion['preference'] in ('higher', 'lower', 'inspect'), 'Explicit criterion preference required')
        identifier(criterion['anchor_evidence_id'], 'evidence')
        choices = criterion['evidence_choices']
        require(isinstance(choices, dict) and set(choices) == set(record['candidate_ids']),
                'Each criterion requires exactly the actual comparison candidate keys')
        for choice in choices.values():
            if choice is not None:
                identifier(choice, 'evidence')


def _resolve(index, key, kind):
    identifier(key, kind)
    record = index.get(key)
    require(record is not None and record['type'] == kind, 'Unknown or wrong-type Decision '+kind+' reference')
    return record


def _scoped_evidence(index, key, candidates):
    record = _resolve(index, key, 'evidence')
    subject = index[record['subject_id']]
    molecule = molecule_id_for(subject, index)
    require(molecule in candidates, 'Decision Evidence belongs outside the actual comparison candidate scope')
    return record, molecule


def _required_snapshot_ids(record, index):
    required = set()
    for criterion in record['criteria']:
        required.add(criterion['anchor_evidence_id'])
        required.update(choice for choice in criterion['evidence_choices'].values() if choice is not None)
    for key in record['hypothesis_ids']:
        hypothesis = _resolve(index, key, 'hypothesis')
        require(set(hypothesis['molecule_ids']) <= set(record['candidate_ids']),
                'Supporting Hypothesis must be entirely within the actual Decision scope')
        required.update(hypothesis['related_evidence_ids'])
    return required


def _review_record(record, index):
    candidates = set(record['candidate_ids'])
    observations = []
    for evidence in index.values():
        if evidence['type'] != 'evidence':
            continue
        molecule = molecule_id_for(index[evidence['subject_id']], index)
        if molecule in candidates:
            observations.append((evidence, molecule))
    criteria, blockers = [], []
    if not record['criteria']:
        blockers.append({'criterion_key': None, 'molecule_id': None, 'reason': 'Define at least one comparison criterion'})
    if not record['chosen_candidate_ids']:
        blockers.append({'criterion_key': None, 'molecule_id': None, 'reason': 'Explicitly choose at least one actual candidate'})
    for criterion in record['criteria']:
        anchor, _ = _scoped_evidence(index, criterion['anchor_evidence_id'], candidates)
        issue = context_issue(anchor)
        require(issue is None, 'Criterion anchor cannot establish an eligible exact context: '+str(issue))
        key = context_key(anchor)
        rows = []
        for candidate in record['candidate_ids']:
            options = [e for e, molecule in observations if molecule == candidate and context_issue(e) is None and context_key(e) == key]
            choice = criterion['evidence_choices'][candidate]
            selected = None
            if choice is not None:
                selected = next((e for e in options if e['id'] == choice), None)
                require(selected is not None, 'Chosen Evidence is stale, incompatible or belongs to another candidate')
            status = ('value missing' if selected is not None and selected['value'] is None else
                      'observed' if selected is not None else 'choose observation' if options else 'no eligible observation')
            if criterion['required'] and (selected is None or selected['value'] is None):
                blockers.append({'criterion_key': criterion['key'], 'molecule_id': candidate, 'reason': status})
            rows.append({'molecule_id': candidate, 'evidence_id': choice, 'subject_id': selected['subject_id'] if selected else None,
                         'value': selected['value'] if selected else None, 'unit': selected['unit'] if selected else None,
                         'status': status, 'options': copy.deepcopy(options)})
        criteria.append({**copy.deepcopy(criterion), 'context': {field: copy.deepcopy(anchor[field]) for field in
                        ('kind', 'metric', 'unit', 'conditions', 'source')}, 'rows': rows})
    predecessor = index.get(record['supersedes'])
    changes = []
    if predecessor is not None:
        for field in ('candidate_ids', 'chosen_candidate_ids', 'criteria', 'hypothesis_ids', 'reason'):
            before, after = predecessor.get(field), record[field]
            if json.dumps(before, sort_keys=True, allow_nan=False) != json.dumps(after, sort_keys=True, allow_nan=False):
                changes.append({'field': field, 'before': copy.deepcopy(before), 'after': copy.deepcopy(after)})
        before = [e['id'] for e in predecessor['evidence_snapshot']]
        after = [e['id'] for e in record['evidence_snapshot']]
        if before != after:
            changes.append({'field': 'snapshot_evidence_ids', 'before': before, 'after': after})
    return {'candidate_ids': copy.deepcopy(record['candidate_ids']), 'criteria': criteria,
            'blockers': blockers, 'ready_to_finalize': not blockers, 'changes': changes,
            'policy': 'Every required criterion needs an explicit numeric observation for every comparison candidate, even when unchosen. Weights do not waive requirements; no score or ranking is computed.'}


def validate_decision_references(index):
    successors = {}
    for record in index.values():
        if record['type'] != 'decision' or is_legacy(record):
            continue
        predecessor = record['supersedes']
        if predecessor is not None:
            previous = _resolve(index, predecessor, 'decision')
            require(record['revision'] == previous['revision'] + 1, 'Decision revision must be exactly predecessor revision + 1')
            require(predecessor not in successors, 'Decision predecessor already has a successor; review the latest version')
            successors[predecessor] = record['id']
        required = _required_snapshot_ids(record, index)
        snapshot_ids = {e['id'] for e in record['evidence_snapshot']}
        require(required <= snapshot_ids, 'Decision snapshot omits a criterion, selected observation or Hypothesis source')
        review = _review_record(record, index)
        if record['status'] == 'finalized' and review['blockers']:
            raise ValidationError('Required Decision information is missing; finalization blocked',
                                  [f"{b['criterion_key'] or 'Decision'} / {b['molecule_id'] or 'scope'}: {b['reason']}" for b in review['blockers']])


def decision_context(bundle, candidate_ids):
    id_list(candidate_ids, 'molecule', 'Comparison candidates', nonempty=True)
    index = {e['id']: e for e in bundle['entities']}
    for candidate in candidate_ids:
        _resolve(index, candidate, 'molecule')
    cohorts, ineligible = {}, []
    for evidence in sorted(index.values(), key=lambda e: e['id']):
        if evidence['type'] != 'evidence' or molecule_id_for(index[evidence['subject_id']], index) not in candidate_ids:
            continue
        issue = context_issue(evidence)
        if issue:
            ineligible.append({'evidence_id': evidence['id'], 'reason': issue})
            continue
        key = context_key(evidence)
        if key not in cohorts:
            cohorts[key] = {'id': evidence['id'], 'evidence_ids': [], **{field: copy.deepcopy(evidence[field]) for field in
                            ('kind', 'metric', 'unit', 'conditions', 'source')}}
        cohorts[key]['evidence_ids'].append(evidence['id'])
    return {'candidate_ids': copy.deepcopy(candidate_ids), 'cohorts': list(cohorts.values()), 'ineligible': ineligible}


def decision_review(bundle, definition):
    fields(definition, {'candidate_ids', 'chosen_candidate_ids', 'criteria', 'hypothesis_ids', 'supporting_evidence_ids',
                        'reason', 'status', 'supersedes'}, 'Decision definition')
    index = validate_extension(bundle['project'], bundle['entities'], [])
    data = copy.deepcopy(definition)
    id_list(data['supporting_evidence_ids'], 'evidence', 'Supporting Evidence')
    require(isinstance(data['criteria'], list) and len(data['criteria']) <= 20, 'Decision supports up to 20 explicit criteria')
    for criterion in data['criteria']:
        fields(criterion, CRITERION_FIELDS, 'Decision criterion')
        # UI supplies the entered decimal text: blank/underflow must not turn into 0.
        # Stored awx/1 weights are numbers; direct JSON import remains strict.
        if isinstance(criterion['weight'], str):
            criterion['weight'] = parse_json(criterion['weight'])
    previous = _resolve(index, data['supersedes'], 'decision') if data['supersedes'] is not None else None
    created = now()
    record = {'id': new_id('decision'), 'type': 'decision', 'project_id': bundle['project']['id'],
              'created_at': created, 'timestamp': created, 'candidate_ids': data['candidate_ids'],
              'chosen_candidate_ids': data['chosen_candidate_ids'], 'criteria': data['criteria'],
              'hypothesis_ids': data['hypothesis_ids'], 'reason': data['reason'], 'status': data['status'],
              'revision': previous['revision'] + 1 if previous else 1, 'supersedes': data['supersedes'],
              'source': {'name': 'Antibody Insight local researcher decision entry', 'version': __version__}, 'evidence_snapshot': []}
    # Validate shape before using caller-supplied choice lists or Hypothesis keys.
    from .domain import validate_entity
    validate_entity(record, bundle['project']['id'])
    needed = _required_snapshot_ids(record, index) | set(data['supporting_evidence_ids'])
    for key in needed:
        _scoped_evidence(index, key, record['candidate_ids'])
    record['evidence_snapshot'] = [copy.deepcopy(index[key]) for key in sorted(needed)]
    validate_extension(bundle['project'], bundle['entities'], [record])
    return {'bundle': {'schema_version': SCHEMA, 'project': copy.deepcopy(bundle['project']), 'entities': [record]},
            'review': _review_record(record, index)}
