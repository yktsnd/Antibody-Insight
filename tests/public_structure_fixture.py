"""Offline, explicit primary Fab A/B in the complete experimental 1MLC source."""

import hashlib
from pathlib import Path

import gemmi

from workspace_app.domain import SCHEMA
from workspace_app.fixtures import STAMP, fixture_id
from workspace_app.structures import RESIDUE_FIELDS, parse_structure


def public_structure_bundle():
    raw=(Path(__file__).resolve().parents[1]/'fixtures/public/1MLC.cif').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='5536c79a3d73e09503f6a4d252bbca2dac5fa0e59b5424309f49cd0c34e8606e'
    content=raw.decode('utf-8'); block=gemmi.cif.read_string(content).sole_block()
    sequences={}
    for row in block.find(['_entity_poly.pdbx_strand_id','_entity_poly.pdbx_seq_one_letter_code_can']):
        sequence=''.join(gemmi.cif.as_string(row[1]).split())
        for chain in row[0].split(','): sequences[chain]=sequence
    project={'id':fixture_id('project','public-1MLC'),'title':'Public experimental 1MLC source inspection',
             'goal':'Offline source/scale validation; not prediction validation','created_at':STAMP,'data_class':'research'}
    def record(kind,**fields):
        return dict(id=fixture_id(kind,'public-1MLC'),type=kind,project_id=project['id'],created_at=STAMP,**fields)
    source={'name':'PDB 1MLC deposited coordinate file; Braden et al.','version':'1.3 / 2024-10-23'}
    molecule=record('molecule',name='D44.1 primary Fab A/B in 1MLC asymmetric unit',external_id='PDB-1MLC-AB',format='declared Fab',source=source,
                    chains=[{'id':c,'role':'deposited light chain' if c=='A' else 'deposited heavy chain','sequence':sequences[c]} for c in ('A','B')])
    structure=record('structure',name='1MLC complete experimental asymmetric unit',molecule_id=molecule['id'],file_format='mmcif',
                     content=content,sha256=hashlib.sha256(raw).hexdigest(),origin_kind='experimental',source=source)
    parsed=parse_structure(content,'mmcif'); assignments=[]; positions=[]
    for chain in parsed['chains']:
        label=chain['label_asym'];role='antibody' if label in ('A','B') else 'antigen' if label in ('E','F') else 'other'
        assignments.append(dict(chain,role=role,molecule_chain_id=label if role=='antibody' else None,
            target_ref={'namespace':'PDB-entity','identifier':'1MLC:3'} if role=='antigen' else None,
            label='Deposited primary Fab chain' if role=='antibody' else 'Deposited lysozyme chain' if role=='antigen' else 'Other deposited Fab copy' if label in ('C','D') else 'Deposited water chain'))
    for residue in parsed['residues']:
        if residue['label_asym'] not in ('A','B'): continue
        assert residue['aa']==sequences[residue['label_asym']][residue['label_number']-1]
        assert residue['altlocs']==['']
        positions.append({'chain_id':residue['label_asym'],'sequence_index':residue['label_number'],'status':'mapped',
                          'structure_residue':{k:residue[k] for k in RESIDUE_FIELDS},'altloc':'','reason':None})
    mapping=record('structure_map',structure_id=structure['id'],molecule_id=molecule['id'],source={'name':'Explicit deposited label_seq_id correspondence, primary Fab A/B','version':'1MLC 1.3'},
                   chain_assignments=assignments,residues=positions)
    return {'schema_version':SCHEMA,'project':project,'entities':[molecule,structure,mapping]}
