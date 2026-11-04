"""Synthetic typed-JSON transport inputs and Python-only evidence inspection."""

import hashlib
import json
import math

from workspace_app.fixtures import example_bundle, fixture_id
from workspace_app.observation import observation_order


def transport_bundle(label):
    bundle=example_bundle(2)
    ids={bundle['project']['id']:fixture_id('project','numeric-transport/'+label)}
    ids.update({e['id']:fixture_id(e['type'],'numeric-transport/'+label+'/'+e['id']) for e in bundle['entities']})
    def remap(value):
        if isinstance(value,str):return ids.get(value,value)
        if isinstance(value,list):return [remap(v) for v in value]
        if isinstance(value,dict):return {k:remap(v) for k,v in value.items()}
        return value
    bundle=remap(bundle)
    bundle['project']['title']='[SYNTHETIC FIXTURE] Numeric transport '+label
    bundle['project']['goal']='Exact typed-context transport investigation only; no physical quantity claim'
    measured=[e for e in bundle['entities'] if e['type']=='evidence' and e['kind']=='measured']
    for evidence,dose in zip(measured,[1,1.0]):
        evidence['metric']='synthetic_transport_context'
        evidence['conditions']={'assay':'SYNTHETIC typed-context check','dose':dose,'nested':{'values':[1,1.0,-0.0,0.0]}}
        evidence['source']={'name':'SYNTHETIC numeric transport fixture, no experiment','version':'1'}
    return bundle


def inspect_transport(document):
    bundle=document.get('bundle',document)
    measured=[e for e in bundle['entities'] if e['type']=='evidence' and e['kind']=='measured']
    def number_tag(value):
        if type(value) is float and value==0:
            return 'negative_float_zero' if math.copysign(1,value)<0 else 'float_zero'
        return type(value).__name__
    canonical=json.dumps(bundle,sort_keys=True,ensure_ascii=False,allow_nan=False)
    return {'canonical_sha256':hashlib.sha256(canonical.encode()).hexdigest(),
            'cohort_count':len(observation_order(bundle)['cohorts']),
            'dose_types':[number_tag(e['conditions']['dose']) for e in measured],
            'nested_types':[[number_tag(v) for v in e['conditions']['nested']['values']] for e in measured]}
