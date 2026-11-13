"""Replay public G14 sequence declarations using the existing Construct contract."""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from openpyxl import load_workbook

from workspace_app.adapters import grouped_fasta_preview, new_project
from workspace_app.domain import ValidationError
from workspace_app.experiments import construct_context, metadata_preview
from workspace_app.storage import Store


ROOT = Path(__file__).resolve().parents[1]
CODE = dict(zip(map(''.join, itertools.product('TCAG', repeat=3)),
                'FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG', strict=True))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(workbook, directory):
    source = json.loads((ROOT / 'validation/prophet-ab-reference-expectations.json').read_text(encoding='utf-8'))
    assert sha(workbook.read_bytes()) == source['input_sha256'], 'Workbook digest does not match the pinned source'
    book = load_workbook(workbook, read_only=True, data_only=True)
    sheet = book[source['sequence_sheet']]
    assert sheet['A111'].value == source['antibody_id']
    assert sheet['B111'].value == source['antibody_name']
    chains = {}
    for role, expected in source['chains'].items():
        proteins, sequences, translations = [], [], []
        for batch in source['production_batches']:
            protein_cell, dna_cell = expected[f'batch_{batch}_cells']
            protein = ''.join(sheet[protein_cell].value.split())
            dna = sheet[dna_cell].value
            assert len(dna) == expected['dna_length'] and len(protein) == expected['source_protein_length']
            translation = ''.join(CODE[dna[index:index + 3]] for index in range(0, len(dna), 3))
            assert translation[3:] == protein and translation.endswith('*') and translation.count('*') == 1
            assert sha(translation.encode('ascii')) == expected['translation_with_stop_sha256']
            proteins.append(protein)
            sequences.append(dna)
            translations.append(translation)
        assert proteins[0] == proteins[1] and translations[0] == translations[1] and sequences[0] != sequences[1]
        chains[role] = (translations[0][:-1], sequences)
    book.close()

    project = new_project('GDPa1-110 published construct comparison', 'Inspect two recorded CDS variants of one chain')
    protein, sequences = chains['heavy']
    raw = f'>{source["antibody_id"]}-HEAVY-TRANSLATION\n{protein}\n'
    result = grouped_fasta_preview(raw, 'derived-gdpa1-heavy-translation.fasta', project, {
        'assignments': [{'record_index': 0, 'external_id': 'GDPa1-110-HEAVY-TRANSLATION', 'chain_id': 'H', 'role': 'heavy'}],
        'text_sha256': sha(raw.encode('ascii')), 'molecular_format': 'Workbook CDS translation, heavy chain only',
    })
    molecule, = result['bundle']['entities']
    store = Store(directory / 'original.sqlite3')
    store.import_bundle(result['bundle'])
    constructs = []
    for batch, dna in zip(source['production_batches'], sequences, strict=True):
        preview = metadata_preview(store.bundle(project['id']), {
            'type': 'construct', 'name': f'GDPa1-110 heavy CDS, workbook production batch {batch}',
            'molecule_id': molecule['id'], 'cds': dna, 'vector': None, 'signal_peptide': None,
        })
        construct, = preview['entities']
        store.import_bundle(preview)
        constructs.append(construct['id'])
    saved = store.bundle(project['id'])
    assert constructs[0] != constructs[1]
    observed = construct_context(saved, molecule['id'], *constructs)
    comparison = observed['comparison']['cds']
    assert comparison['status'] == 'different_recorded_values'
    assert len(comparison['raw_differences']) == source['chains']['heavy']['raw_dna_differences']
    assert not observed['observations'] and not observed['materials']
    try:
        construct_context(saved, molecule['id'], constructs[0], constructs[0])
    except ValidationError as error:
        assert 'two distinct actual Construct IDs' in str(error)
    else:
        raise AssertionError('One actual Construct was accepted as both sides')

    fresh = Store(directory / 'restored.sqlite3')
    fresh.import_bundle(saved)
    assert Store(store.path).bundle(project['id']) == fresh.bundle(project['id']) == saved
    return {'status': 'PASS', 'source_sha256': source['input_sha256'],
            'scope': 'Public workbook translation check and heavy-chain Construct comparison',
            'different_raw_dna_positions': len(comparison['raw_differences']),
            'distinct_constructs_preserved': True, 'same_construct_pair_rejected': True,
            'original_and_restored_stores_equal': True, 'measured_observations_imported': 0,
            'human_scientific_review': 'pending'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workbook', type=Path)
    args = parser.parse_args()
    with TemporaryDirectory(prefix='awx-gdpa1-') as directory:
        print(json.dumps(run(args.workbook, Path(directory)), indent=2))
