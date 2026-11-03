"""Independent F12/F13 boundary geometry; no biological or chemical interpretation."""

import hashlib

from workspace_app.domain import SCHEMA
from workspace_app.fixtures import STAMP, fixture_id
from workspace_app.structures import RESIDUE_FIELDS, parse_structure


def boundary_bundle():
    project={'id':fixture_id('project','independent-observation-boundary'),'title':'[SYNTHETIC FIXTURE] Independent representation boundaries',
             'goal':'Geometry and exact source identity only; no predictor or experiment','created_at':STAMP,'data_class':'synthetic_fixture'}
    def record(entity_type,**fields):
        return dict(id=fixture_id(entity_type,'independent-observation-boundary'),type=entity_type,project_id=project['id'],created_at=STAMP,**fields)
    source={'name':'SYNTHETIC independent geometry fixture','version':'1'}
    molecule=record('molecule',name='Independent boundary candidate',external_id='INDEPENDENT-OBS',format='synthetic fragment',source=source,
                    chains=[{'id':'H','role':'declared synthetic antibody chain','sequence':'AFSAAG'}])
    # A calcium ion is physically in front of the visible protein CA at the same x/y.
    # A/B share a common atom, but cannot bond to each other. Unknown values stay unknown.
    atoms=[('C','CA','.','ALA','H',1,0,0,0),('C','CB','.','ALA','H',1,1.5,0,0),
           ('C','CA','A','PHE','H',2,4,0,0),('C','CA','B','PHE','H',2,4,1,0),('C','C','.','PHE','H',2,5.4,.5,0),
           ('O','O','.','SER','H',3,8,0,0),
           ('Ca','CA','.','CA','I',1,0,0,8),('C','CA','.','MSE','M',1,12,0,0),
           ('C','CA','?','ALA','H',4,16,0,0),('C','CB','.','ALA','H',4,17.5,0,0),
           ('?','CA','.','ALA','H',5,20,0,0),('C','CB','.','ALA','H',5,21.5,0,0)]
    tags='group_PDB id type_symbol label_atom_id label_alt_id label_comp_id label_asym_id label_seq_id pdbx_PDB_ins_code Cartn_x Cartn_y Cartn_z occupancy B_iso_or_equiv auth_seq_id auth_comp_id auth_asym_id pdbx_PDB_model_num'.split()
    lines=['data_independent_boundary','loop_',*('_atom_site.'+tag for tag in tags)]
    for i,(element,atom,alt,resname,chain,number,x,y,z) in enumerate(atoms,1):
        lines.append(' '.join(map(str,['HETATM' if chain in ('I','M') else 'ATOM',i,element,atom,alt,resname,chain,number,'.',x,y,z,'?','?',number,resname,chain,1])))
    content='\n'.join(lines)+'\n'
    structure=record('structure',name='Independent source alternate/element/overview boundaries',molecule_id=molecule['id'],file_format='mmcif',
                     content=content,sha256=hashlib.sha256(content.encode()).hexdigest(),origin_kind='unknown',source=source)
    parsed=parse_structure(content,'mmcif')
    mapping=record('structure_map',structure_id=structure['id'],molecule_id=molecule['id'],source=source,
                   chain_assignments=[dict(chain,role='antibody' if chain['auth_chain']=='H' else 'other',molecule_chain_id='H' if chain['auth_chain']=='H' else None,target_ref=None,label='Explicit independent fixture declaration') for chain in parsed['chains']],
                   residues=[{'chain_id':'H','sequence_index':r['auth_number'],'status':'mapped','structure_residue':{k:r[k] for k in RESIDUE_FIELDS},'altloc':'A' if r['auth_number']==2 else '','reason':None} for r in parsed['residues'] if r['auth_chain']=='H' and r['auth_number']<=3]+
                            [{'chain_id':'H','sequence_index':6,'status':'unavailable','structure_residue':None,'altloc':'','reason':'No source atoms for this sequence position'}])
    note=record('evidence',subject_id=molecule['id'],kind='annotation',metric='source_note',value=None,unit=None,conditions=None,
                source=source,timestamp=STAMP,description='<img src=x onerror="invent()"> Source text, not an automatically classified concern.',
                residue_refs=[{'chain_id':'H','sequence_index':2}])
    return {'schema_version':SCHEMA,'project':project,'entities':[molecule,structure,mapping,note]}
