"""F14/F15, P05/J05/AC-J05: explicit recipes, not predicted molecular assembly."""

import copy

from . import __version__
from .composition import composition_signature
from .domain import SCHEMA, fields, identifier, new_id, now, nullable_text, require, sequence, text, validate_graph


def _source_component(part, index):
    fields(part, {'id', 'role', 'source'}, 'composition component')
    origin = part['source']
    require(isinstance(origin, dict), 'An explicit component source is required')
    if origin.get('kind') == 'sequence':
        fields(origin, {'kind', 'sequence'}, 'independent sequence source')
        sequence(origin['sequence'], 'Independent component sequence')
        component_sequence, reference = origin['sequence'], None
    else:
        require(origin.get('kind') == 'binding_unit', 'Unsupported component source; choose an explicit sequence or BindingUnit interval')
        fields(origin, {'kind', 'binding_unit_id', 'chain_id', 'start', 'end'}, 'BindingUnit interval source')
        identifier(origin['binding_unit_id'], 'binding_unit')
        unit = index.get(origin['binding_unit_id'])
        require(unit is not None and unit['type'] == 'binding_unit', 'Unknown or wrong-type BindingUnit source in this project')
        text(origin['chain_id'], 'Source chain', 100)
        chain = next((c for c in unit['chains'] if c['id'] == origin['chain_id']), None)
        require(chain is not None, 'The named source chain is absent from this BindingUnit')
        start, end = origin['start'], origin['end']
        require(type(start) is int and type(end) is int and chain is not None and 1 <= start <= end <= len(chain['sequence']),
                'Source interval must be an existing inclusive 1-based integer range; no nearest interval is substituted')
        component_sequence = chain['sequence'][start - 1:end]
        reference = {k: copy.deepcopy(origin[k]) for k in ('binding_unit_id', 'chain_id', 'start', 'end')}
    return {'id': part['id'], 'role': part['role'], 'sequence': component_sequence, 'origin': reference}


def composition_preview(bundle, definition):
    """Resolve exact sources and review new immutable records without saving them."""
    fields(definition, {'name', 'external_id', 'format', 'chains', 'connections', 'parent_id', 'reason', 'note'}, 'composition definition')
    index = {e['id']: e for e in bundle['entities']}
    require(isinstance(definition['chains'], list) and 0 < len(definition['chains']) <= 100, 'Define 1–100 explicit chains; none is inferred')
    require(isinstance(definition['connections'], list) and len(definition['connections']) <= 5000, 'Explicit connection list required')
    nullable_text(definition['note'], 'Researcher annotation')
    nullable_text(definition['reason'], 'Composition lineage reason')
    parent = None
    if definition['parent_id'] is None:
        require(definition['reason'] is None, 'A lineage reason needs an explicitly chosen parent; use the annotation field for a new independent design')
    else:
        identifier(definition['parent_id'], 'molecule')
        parent = index.get(definition['parent_id'])
        require(parent is not None and parent['type'] == 'molecule', 'Unknown or wrong-type composition parent in this project')
        text(definition['reason'], 'Composition lineage reason')
    chains, graph_chains = [], []
    for declared in definition['chains']:
        fields(declared, {'id', 'role', 'copies', 'components'}, 'explicit composition chain')
        parts = declared['components']
        require(isinstance(parts, list) and 0 < len(parts) <= 1000, 'Each chain needs an explicit ordered nonempty component list')
        components, length = [], 0
        for part in parts:
            component = _source_component(part, index)
            length += len(component['sequence'])
            require(length <= 100000, 'Assembled chain exceeds the 100000-residue sequence limit')
            components.append(component)
        chains.append({'id': declared['id'], 'role': declared['role'], 'sequence': ''.join(p['sequence'] for p in components)})
        graph_chains.append({'chain_id': declared['id'], 'copies': declared['copies'], 'components': components})
    stamp = now(); source = {'name': 'Antibody Insight local researcher composition entry', 'version': __version__}
    common = {'project_id': bundle['project']['id'], 'created_at': stamp}
    molecule = {**common, 'id': new_id('molecule'), 'type': 'molecule', 'name': definition['name'], 'external_id': definition['external_id'],
                'format': definition['format'], 'chains': chains, 'source': source,
                'component_graph': {'chains': graph_chains, 'connections': copy.deepcopy(definition['connections'])}}
    records = [molecule]
    if parent is not None:
        records.append({**common, 'id': new_id('lineage'), 'type': 'lineage', 'parent_id': parent['id'], 'child_id': molecule['id'],
                        'change_set': {'kind': 'composition', 'reason': definition['reason'],
                                       'before': composition_signature(parent), 'after': composition_signature(molecule)}})
    if definition['note'] is not None:
        records.append({**common, 'id': new_id('evidence'), 'type': 'evidence', 'subject_id': molecule['id'], 'kind': 'annotation',
                        'metric': 'composition_design_note', 'description': definition['note'], 'source': copy.deepcopy(source),
                        'timestamp': stamp, 'conditions': None, 'value': None, 'unit': None})
    validate_graph(bundle['project'], [*bundle['entities'], *records])
    return {'schema_version': SCHEMA, 'project': copy.deepcopy(bundle['project']), 'entities': records}


def composition_context(bundle, molecule_id):
    """Expose actual source usages, never complete functional units or valency."""
    identifier(molecule_id, 'molecule')
    index = {e['id']: e for e in bundle['entities']}; molecule = index.get(molecule_id)
    require(molecule is not None and molecule['type'] == 'molecule', 'Unknown or wrong-type composition molecule')
    graph = molecule.get('component_graph')
    result = {'molecule': copy.deepcopy(molecule), 'status': 'declared' if graph is not None else 'undefined', 'source_units': []}
    if graph is None:
        return result
    units = {}
    for chain in graph['chains']:
        for component in chain['components']:
            origin = component['origin']
            if origin is None:
                continue
            unit = index[origin['binding_unit_id']]
            if unit['id'] not in units:
                units[unit['id']] = {'unit': copy.deepcopy(unit), 'chains': [
                    {'chain_id': c['id'], 'source_length': len(c['sequence']), 'usages': [], 'full_source_chain_occurrences': 0} for c in unit['chains']]}
            context = next(c for c in units[unit['id']]['chains'] if c['chain_id'] == origin['chain_id'])
            full = origin['start'] == 1 and origin['end'] == context['source_length']
            context['usages'].append({'molecule_chain_id': chain['chain_id'], 'component_id': component['id'], 'copies': chain['copies'],
                                     'start': origin['start'], 'end': origin['end'], 'is_full_source_chain': full})
            if full:
                context['full_source_chain_occurrences'] += chain['copies']
    result['source_units'] = list(units.values())
    return result
