# P0 residue correspondence: independent scoped review

- Reviewer: `/root/mapping_review`, separate from the implementation agent.
- Review recorded: 2026-11-10, 20:04 JST.
- Trace: P03/P04/P08; J03/J04/J08; AC-J03/AC-J04/AC-J08.
- Scoped P0 result: **PASS** for the source hashes in `M6-mapping-independent-browser-v5.json` and `M6-mapping-independent-domain-v2.json`.
- Whole milestone integration: **NEEDS-EVIDENCE** until the final combined source and prescribed eight main / sixteen negative journeys are independently replayed. This report does not accept the other P1 fixes, real-data core workflow, scientific validity or Release1.0.

The researcher must be able to ask which actual coordinate supports a residue-level observation or proposed variant. An order-consistent correspondence is necessary for that task. It does not prove an alignment biologically correct or resolve an identical-repeat offset. Human scientific goldens and real-antibody workflow validation remain required. The largest product gap remains preparing and using a researcher's ordinary multichain inputs through design and reasoned next action; this targeted repair preserves that goal rather than replacing it with validation counts.

## Independent replay

`M6-mapping-independent-probe.py` creates its own minimal synthetic PDB/mmCIF cases and temporary databases. The second domain replay passed **10/10** independent probes:

1. Reversed identical PDB residues reject graph validation and atomic import.
2. Reversed identical mmCIF residues reject by polymer-label order.
3. A correct PDB map with a missing raw position and author insertion code persists exactly.
4. Descending author numbers are not incorrectly sorted into sequence order.
5. Shuffled mmCIF atom rows with descending author IDs use polymer labels correctly.
6. A single source residue with a missing mmCIF polymer label cannot drive sequence highlighting.
7. Duplicated polymer labels under distinct author loci remain unverified.
8. A source chain repeated across TER partitions cannot establish a cross-part order.
9. A legacy contradictory map is source-only without source mutation; an unrelated shortlist can still be saved.
10. A new hypothesis cannot assert a quarantined map. An explicitly source-only structure reference remains possible.

`M6-mapping-independent-browser.cjs` starts a separate local server with an isolated temporary legacy database. Chrome/Playwright uses actual local WebGL and mouse interaction. Replay v5 passed eight API/UI cases plus the zero-browser-error / zero-external-request check:

- API preview rejects the inverse identical-residue map.
- Native awx file preview rejects both complete-project and append-file inverse maps before saving; all prior entities remain exact.
- A direct new-map import rejects atomically, preserving every existing entity.
- A stored inverse map displays its warning. A sequence click has zero selected source atoms and disables coordinate focus.
- Clicking the actual atom of that source remains source-only, selects no sequence residue and yields a hypothesis context with `structure_map_id=null`.
- Constructing the two reversed pairs in the ordinary correspondence editor fails before a Save control is offered.
- A distinct gap-bearing molecule preserves its identity; its correct map passes API preview and save.
- Sequence index3 highlights exact author10 insertionA; clicking actual author15 selects raw index4.

The retained suites were also independently executed:

```
.venv/Scripts/python.exe -m pytest tests/test_structures.py tests/test_structures_independent.py tests/test_design_hypotheses_independent.py -q
60 passed in 8.70s
```

Commands for the stored new probes:

```
.venv/Scripts/python.exe TEST_EVIDENCE/M6-mapping-independent-probe.py --output TEST_EVIDENCE/M6-mapping-independent-domain-v2.json
node TEST_EVIDENCE/M6-mapping-independent-browser.cjs TEST_EVIDENCE/M6-mapping-independent-browser-v5.json
```

The Node command uses the installed Playwright dependency via `NODE_PATH`, and `PYTHON` points to the workspace virtual environment. Each output path must be new; the runners reject an existing destination.

## Design, scientific references and mandatory gates

The repair reuses source parsing and a shared validation function. No alignment algorithm, coordinate renumbering, new molecular identity or data migration is introduced. This is smaller and more transparent than inferring correspondence from equal amino acids.

PDB protein ATOM order is defined from amino to carboxyl terminus and TER terminates the chain. Author numbering and insertion code identify a source residue; numeric sorting is not a scientific sequence-order guarantee. The implementation uses the source encounter order within the exact model/chain/segment/TER partition and withholds ambiguous cases. [wwPDB PDB format3.3, ATOM and TER](https://www.wwpdb.org/documentation/file-format-content/format33/sect9.html)

For mmCIF, `label_seq_id` points to `entity_poly_seq.num`. Source author IDs and physical atom-row order remain distinct from that polymer position. The implementation conservatively requires an available positive unambiguous label within model/label-asym scope. [wwPDB item definition](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_atom_site.label_seq_id.html)

- Identity: existing shape/reference/amino-acid/conformer/locus checks remain active. Only trusted stored IDs receive the legacy order exemption; HTTP payloads cannot declare exemptions. Duplicate incoming IDs still reject. The order check follows the existing locus checks, preserving their diagnostics.
- Provenance: read-time quarantine does not rewrite original map/source records. New map/hypothesis validation prevents a quarantined association being introduced as a new accepted mapping context.
- Security: the independent browser replay observed no external requests. Temporary synthetic databases were used. No original research database or existing evidence artifact was modified.
- Regression: sixty retained targeted tests passed. The prescribed eight main journeys and sixteen negative paths remain a separate final integration requirement.

Conservative limitation: any unknown/contradictory portion suppresses linking for the entire selected map. Source coordinates remain inspectable. A legacy contradictory map is retained for provenance but cannot be reimported as a new valid map; unrelated local operations continue. Order consistency alone cannot validate an arbitrary user-declared biological mapping.

## Harness diagnostics retained

The file named `M6-mapping-independent-baseline.json` was run after the implementation patch had already arrived. It is **not baseline product evidence**. Its first eight probes passed; the final probe assertions completed but temporary SQLite cleanup failed because this reviewer's harness had not explicitly closed its connection. The harness now uses `closing()`.

Browser v1 stopped when this reviewer's generated structure ID used `str_` instead of the schema's `stc_` prefix. Browser v2 stopped after the actual valid selection succeeded because the harness checked an unsupported `aria-pressed` attribute rather than the existing active class. These are harness corrections, not implementation changes. Their diagnostic files remain preserved. v3 passed, v4 adds ordinary GUI inverse-pair entry and passes, and v5 adds strict native-file preview checks and passes. No earlier milestone evidence was overwritten.
