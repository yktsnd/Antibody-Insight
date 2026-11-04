"""Explicit synthetic transfer dependencies, not observations or actual designs.

The four source formats and actual metadata are imported through browser controls.
This supplementary awx file tests unrelated dependency closure during J08 transfer;
the design and hypothesis entry journeys are independently exercised in J02–J07.
"""
import copy

from workspace_app.composition import composition_signature
from workspace_app.domain import new_id, now, validate_graph
from workspace_app.hypotheses import hypothesis_preview


def transfer_dependencies(bundle):
    parent = next(e for e in bundle['entities'] if e['type'] == 'molecule')
    structure = next(e for e in bundle['entities'] if e['type'] == 'structure')
    mapping = next(e for e in bundle['entities'] if e['type'] == 'structure_map')
    child = copy.deepcopy(parent)
    child.update(id=new_id('molecule'), external_id='SYNTHETIC-TRANSFER-CHILD',
                 name='SYNTHETIC alternate declared format; not validated assembly',
                 format='SYNTHETIC alternative format declaration', created_at=now(),
                 source={'name': 'SYNTHETIC J08 transfer dependency fixture', 'version': '1'})
    lineage = {'id': new_id('lineage'), 'type': 'lineage', 'project_id': bundle['project']['id'],
               'created_at': now(), 'parent_id': parent['id'], 'child_id': child['id'],
               'change_set': {'kind': 'composition', 'reason': 'SYNTHETIC format declaration for transfer only; no assembly or functional claim',
                              'before': composition_signature(parent), 'after': composition_signature(child)}}
    intermediate = {**bundle, 'entities': [*bundle['entities'], child, lineage]}
    evidence = [e['id'] for e in bundle['entities'] if e['type'] == 'evidence']
    definition = {'molecule_ids': [parent['id'], child['id']], 'related_evidence_ids': evidence,
                  'lineage_ids': [lineage['id']], 'residue_refs': [],
                  'structure_refs': [{'structure_id': structure['id'], 'model': 1, 'structure_map_id': mapping['id']}],
                  'text': 'SYNTHETIC proposed question; no inference from imported values',
                  'question': 'Test the separately declared format using new actual materials and matched protocols',
                  'limitations': 'Synthetic transfer fixture; no biological or external model validation'}
    hypothesis = hypothesis_preview(intermediate, definition)['entities'][0]
    result = {**bundle, 'entities': [child, lineage, hypothesis]}
    validate_graph(bundle['project'], [*bundle['entities'], *result['entities']])
    return result
