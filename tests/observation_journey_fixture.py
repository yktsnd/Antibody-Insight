"""Clearly synthetic J03/J04 workflow inputs; no biological claims or prediction run."""

from workspace_app.fixtures import STAMP, fixture_id
from workspace_app.structure_fixtures import structure_bundle


def observation_journey_bundle():
    bundle=structure_bundle()
    bundle['project']['title']='[SYNTHETIC FIXTURE] J03/J04 connected observation'
    second_structure=[e for e in bundle['entities'] if e['type']=='structure'][1]
    for model,value in ((1,.75),(2,.55)):
        bundle['entities'].append({'id':fixture_id('evidence',f'observation-second-model-{model}'),'type':'evidence',
            'project_id':bundle['project']['id'],'created_at':STAMP,'subject_id':second_structure['id'],'kind':'computed','metric':'ipTM',
            'source':{'name':'SYNTHETIC second metric; no AlphaFold run','version':'1'},'timestamp':STAMP,
            'conditions':{'structure_model':model,'purpose':'synthetic model-scope check'},'value':value,'unit':'1'})
    for i,molecule in enumerate([e for e in bundle['entities'] if e['type']=='molecule']):
        def record(entity_type,label,**fields):
            return dict(id=fixture_id(entity_type,f'observation-journey-{i}-{label}'),type=entity_type,project_id=bundle['project']['id'],created_at=STAMP,**fields)
        construct=record('construct','construct',name=f'Synthetic expression construct {i+1}',molecule_id=molecule['id'],vector='synthetic vector',signal_peptide=None,cds=None)
        material=record('material','material',construct_id=construct['id'],name=f'Synthetic SEC material {i+1}',lot=f'SYNTHETIC lot {i+1}')
        evidence=record('evidence','sec',subject_id=material['id'],kind='measured',metric='aggregate_fraction',value=12 if i==0 else 4,unit='%',
                        conditions={'assay':'SEC','buffer':'synthetic PBS','temperature_C':25},source={'name':'SYNTHETIC SEC measurements; no experiment executed','version':'1'},timestamp=STAMP)
        concern=record('evidence','position-note',subject_id=molecule['id'],kind='computed',metric='source_reported_note',value=None,unit=None,
                       conditions={'method':'synthetic position-report fixture; no predictor executed'},source={'name':'SYNTHETIC position-report fixture','version':'1'},timestamp=STAMP,
                       description='Synthetic proposed concern at H raw 5; neither causality nor an experimental residue effect has been established.',
                       residue_refs=[{'chain_id':'H','sequence_index':5}])
        numbering=record('residue_map','partial-map',molecule_id=molecule['id'],chain_id='H',domain_id='synthetic-partial-V',chain_type='heavy',scheme='IMGT',definition='rearranged_v_domain',
                         status='mapped',reason='Only six synthetic observed coordinates; not a complete antibody domain',sequence_start=1,sequence_end=6,
                         source={'name':'SYNTHETIC imported coordinates, not assigned by IMGT','version':'1'},
                         verification={'status':'engineering_fixture','reference':'Engineering consistency only; not human scientific validation','reviewer':None,'reviewed_at':None},
                         entries=[{'sequence_index':j,'number':j,'ins_code':'','aa':aa} for j,aa in enumerate(molecule['chains'][0]['sequence'],1)])
        bundle['entities'].extend([construct,material,evidence,concern,numbering])
        if i==0:
            bundle['entities'].extend([{**evidence,'id':fixture_id('evidence','observation-unit-fraction'),'unit':'1','value':.12},
                {**evidence,'id':fixture_id('evidence','observation-unknown-conditions'),'conditions':None,'value':99}])
    return bundle
