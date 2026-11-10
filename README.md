# Antibody Insight

A local research workspace connecting antibody candidates to sequences, materials, evidence and the reasoning behind a selection.

[日本語の利用ガイド](README.ja.md) · [Product goal](PRODUCT_GOAL.md) · [Development specification](DEVELOPMENT_PLAN.md) · [Current limitations](KNOWN_LIMITATIONS.md)

**Development build0.8.0-dev. Historical engineering checkpoint:** All eight prescribed synthetic engineering journeys and sixteen specified negatives passed independent replay on the same frozen source (`a82cc0f`). F01–F22 connect exploration, source-numbered design, structural reasoning, property-driven variants, explicit composition, original construct/material observations, immutable decisions and source-preserving complete project transfer. [Independent review](TEST_EVIDENCE/M5-final-independent-review.md) · [Release gates](TEST_EVIDENCE/M5-release-gates.json). M5 overall quality integration and Release1.0 remain incomplete: standard-hardware latency, eighteen human-verified scientific examples and actual researcher evaluation remain open. No predictive model or automatic numbering engine is executed here.

The latest source-preserving computed JSON import explicitly records actual subjects/model IDs and retains the complete submitted JSON, unmapped fields, source/hash and value pointers. Native project export/fresh-store reimport preserves those records, typed values, original correspondence, proposed hypotheses and fixed Decision versions. Reconstruction does not rerun or authenticate an external computation. The current8GB host measured simple-operation p95≈327ms after a bounded selection improvement; this exceeds300ms and does not qualify the specified16GB/SSD performance gate. [Human validation packet](validation/README.md).

Version0.7.0-dev adds J07 criterion-bearing Decision drafts/finalized revisions in R. Independent design/domain/API/UI and frozen J01–J07 integration passed at source commit `b7eabac`. Explicit required observations, original source snapshots and separate immutable revisions survive actual restart and native fresh export/reimport. M4 meets its engineering gate; the whole product remains unfinished. [Decision data contract](docs/DECISION_CONTRACT.md).

Current product review: **FAIL** on7d691b2 despite the historical8/16. M6 corrects source-order correspondence and lost shortlist input, and adds a paired research example plus explicit chain grouping for your FASTA. [Final independent M6 engineering replay](TEST_EVIDENCE/M6-final-independent-review.md) PASS:549 Python tests,26 Node commands and8/16 prescribed paths on source057b3e9. [Current gates](TEST_EVIDENCE/M6-release-gates.json). The complete real-antibody input→observation→design→experiment→decision action, scientific validity and researcher usefulness remain open. See [revised development plan9.2](DEVELOPMENT_PLAN.md), [real-data validation](docs/CORE_RESEARCH_VALIDATION.md) and [current progress](docs/PROGRESS.md).

## Run locally

Requires Python 3.12 or later and a local browser. SQLite and the application API use Python's standard library; the structural parser is pinned Gemmi0.7.5. The pinned 3Dmol viewer is already included and served locally. No external analysis service is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\start.ps1
```

Open [the local workspace](http://127.0.0.1:8765). To stop, press Ctrl+C in the terminal. The startup script uses the local virtual environment when present. You can also run `.\.venv\Scripts\python.exe -m workspace_app.server` directly. Installing dependencies downloads public packages; running the application performs no external transmission.

The default database is `%LOCALAPPDATA%/AntibodyInsight/workspace.sqlite3` on Windows, outside this OneDrive checkout. On other platforms it is under `~/.local/share/AntibodyInsight/`. Use `--database PATH --port PORT` to run an isolated workspace. Do not use the development server as a shared or internet-facing service.

## First research action

1. On an empty workspace, open **Explore two paired candidates — synthetic example**, review and save, then compare H/L chains and original sample conditions. For your own files, choose **Import data**. Select **FASTA (explicit candidate / chain grouping)** to assign each record to a declared candidate/chain/role. Ordinary FASTA remains unpaired.
2. Review the valid/excluded rows, sequence repeats, source and target project. Explicitly save the valid records.
3. Select candidates in **E**. Inspect chains and raw sequence positions in **W**. The positions are unaligned indexes, not verified IMGT positions.
4. In **R**, inspect measured/computed labels, source, event time, conditions and the Material → Construct → Molecule path. Record the reason for a shortlist, preview the IDs and evidence, then save a draft.
5. Restart the server and reopen the workspace. Saved records and drafts persist. **Export JSON** creates an explicit local download suitable for reimport into an empty database.

Use The format-specific engineering fixtures are under **Format-specific engineering fixtures** in Import data. **Preview composition fixture** to inspect two explicitly declared binding units, ordered components/linker, chain copy counts and composition lineage in W. Origin IDs and before/after signatures remain intact after restart and reimport. The declaration does not validate physical assembly, chemical connectivity or binding.

Use **Preview numbering fixture** for explicitly synthetic IMGT annotations. W separates raw indexes, imported IMGT coordinates, domain IDs and verification states. E can group complete heavy-chain CDR3 sequences using eligible imported maps; multiple map versions/domains require an explicit choice. Unknown, truncated, unverified and failed maps remain visible. No sequence is sent to a numbering service.

Use **Preview structure fixture** to inspect two synthetic complexes from PDB and mmCIF, choose the actual source model, inspect declared antibody/antigen chains, and click real rendered atoms to select their explicitly mapped sequence positions. Missing coordinates and unselected conformers remain unmapped. **Create correspondence revision** lets you explicitly declare chain roles and add/review residue pairs before saving an immutable map. For your own files, import sequences first, choose PDB/mmCIF in E and select the source's declared molecule; no chain or residue match is inferred.

The viewers can link rotation and zoom while retaining separate centers. This is not structural superposition. Supplied model scores retain their source/model scope; missing scores, occupancy and B-fields stay unknown. B-values are not automatically relabeled as confidence. Current limits are24MiB and100,000 atoms per coordinate file; ambiguous reused PDB residue loci across TER and hybrid-36 identifiers report explicit errors rather than partial loading.

**D** creates explicit source-numbered substitutions with a before/after preview and immutable parent/child lineage. Select a mapped residue in W and choose **Design a substitution**, or choose the parent/map in D. An optional reference comparison preserves its source and gaps. The child receives no parent measurements, structures or verified numbering. In R, **Record research hypothesis** retains the proposal, original Evidence, limitations and next experiment. Explicit composition recipes are available in D; R supports criteria, finalization and immutable decision revisions. The researcher guide in the application switches between English and Japanese. UI labels, code and identifiers use English. Japanese explanations use curated antibody-research terminology.

Source-reported position links in W/R navigate to the original molecule/chain/raw index while retaining the Evidence subject, kind, note and conditions. The association does not establish residue-localized measurement or causality. W offers atom, distance-based ball-and-stick and standard amino-acid C-alpha atom views, plus exact-source focus. Source-only selections remain distinct from antibody sequence correspondence. Reviewed hypotheses can retain the actual source file/model/residue/alternate state. F12/F13 and full synthetic J03/J04 passed independent verification. The public experimental 1MLC fixture separately verifies antibody-scale rendering and source preservation; it does not validate a predictor or replace researcher evaluation.

In E, select BindingUnit source IDs and choose **Design an explicit composition**. In D, specify actual chains/roles/copies, ordered source intervals and literal component/linker sequences. Review missing partner usage, partial intervals, occurrence imbalance and exact source IDs before saving. W inspects saved chains and original sources; D compares two actual saved compositions. An explicit parent recipe preserves component IDs and composition Lineage. R retains unverified questions and the next experiment. Declared source-chain occurrences do not establish functional units, valency or physical assembly.

## Import contracts

- FASTA: one header/sequence record creates one unpaired molecule with `format=unspecified` and `role=unknown`. Pairing, molecular format and biological function are not inferred.
- Sequence CSV: `external_id,name,sequence` are required. Optional columns are `chain_role,format`. This is not the measurement CSV importer.
- Measurement CSV: `material_ref,metric,value,unit,timestamp` are required. Optional `conditions_json,description` and paired `source_name,source_version`. Use actual Material IDs or explicitly map external tokens after preview; no candidate/lot-name fallback. Keep original units, conditions and timezone-bearing event times. [Full contract](docs/MEASUREMENT_CONTRACT.md).
- Workspace JSON: versioned `awx/1` with strict entity/reference validation. Measured evidence requires a Material ID. Missing values/conditions remain null; zero remains zero. Unknown source version stays null.
- ID collisions reject the entire save. Unknown fields are reported rather than discarded. Entities and draft snapshots are append-only. An existing project can accept new entities only with unchanged project metadata.

Contextual numeric ordering (F09) and the synthetic J01 engineering path passed independent replay. In E choose an observation context and direction; choose an actual Evidence record when several materials have matching context. Original units, conditions, measured/computed types and source versions remain separate. Missing values follow numbers, and zero stays zero. This does not establish scientific comparability or recommend a candidate.

See the [scientific UX references and reuse decisions](docs/SCIENTIFIC_UX.md), [design contract](docs/DESIGN_CONTRACT.md) and [the language policy and terminology](docs/LANGUAGE_POLICY.md) and [the observation contract](docs/OBSERVATION_CONTRACT.md).

See [the data contract](docs/DATA_CONTRACT.md), [composition contract](docs/COMPONENT_CONTRACT.md), [numbering contract](docs/NUMBERING_CONTRACT.md) and [structure contract](docs/STRUCTURE_CONTRACT.md). Stored component graphs, composition lineage, source-bearing IMGT maps and explicit structure correspondence are supported. The initial IMGT insertion subset is111/112 decimal extensions; other legitimate additions are explicitly unsupported. Interactive composition recipes are supported. Criteria-based final decisions are supported under the [decision contract](docs/DECISION_CONTRACT.md). Canonical computed JSON and native AlphaFold3 summary scalars are available under the [computed JSON contract](docs/PREDICTION_IMPORT_CONTRACT.md); arbitrary native array interpretation and AIRR are unsupported. Measurement CSV follows the [measurement contract](docs/MEASUREMENT_CONTRACT.md). F10/F11 numbered substitutions and proposed hypotheses passed independent verification in the J02 engineering path.

## Verify

Development tests require pytest (MIT). Browser tests require Node.js, Playwright (Apache-2.0) and installed Chrome. These are test dependencies only.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
$env:PYTHON = (Resolve-Path .venv/Scripts/python.exe).Path
node tests/browser.cjs
node tests/numbering-browser.cjs
node tests/structures-browser.cjs
node tests/j01-browser.cjs
node tests/j02-browser.cjs
node tests/j05-browser.cjs
node tests/composition-independent-browser.cjs
node tests/observation-journeys-browser.cjs
python scripts/check_traceability.py
```

If Playwright is supplied by a separate runtime, set `NODE_PATH` to that runtime's `node_modules` directory. `PYTHON` can select the Python executable and `PLAYWRIGHT_CHANNEL` can select an installed Playwright browser channel. The browser test creates temporary databases and runs its own loopback servers. It does not access the user's research database.

The initial browser suite verifies import preview/QC, 800 records, five selections across E/W/D/R, selected-candidate focus, null versus zero, evidence snapshots, a real process restart, JSON roundtrip, hostile text escaping, no outbound browser requests, a mobile viewport and bilingual explanations. These checks are partial-path evidence and must not be counted as final 8/8 or 16/16 acceptance.

The numbering suite uses 800 synthetic candidates to verify CDR-H3 grouping, chain-specific insertion coordinates, explicit ambiguous-map selection, unavailable/partial/unverified states, map-choice restart persistence and ID-only group-filter storage. Engineering fixture success is not human scientific validation.

The structural suite performs actual PDB and mmCIF canvas clicks, raw file import/manual correspondence creation, reciprocal sequence selection, unavailable/alternate handling, physical rotation and wheel zoom, model-score scope/cache refresh, unknown source models, project isolation and restart/roundtrip. Its temporary Chrome profile uses software WebGL for deterministic tests; the application uses the browser's available WebGL implementation.

The dedicated J01 suite verifies CSV800/QC → CDR-H3 and binding context → two-candidate observation → five-ID reason/evidence → actual restart. Independent review confirms this engineering path; scientific golden validation and real researcher evaluation remain pending. See the [product alignment checkpoint](docs/PRODUCT_ALIGNMENT.md) ([日本語](docs/PRODUCT_ALIGNMENT.ja.md)).

See [test evidence](TEST_EVIDENCE/README.md), [traceability](TRACEABILITY.csv), [the initial review](docs/INITIAL_REVIEW.md) and [the acceptance plan](docs/ACCEPTANCE.md). Human-validated scientific golden fixtures and researcher evaluations remain outstanding.

## Architecture

`web/` owns the four-screen UI and local selection state. `workspace_app/domain.py` owns identity/provenance constraints, `storage.py` owns SQLite transactions, and `adapters.py` owns input formats. The loopback API validates Host, Origin, session and CSRF token, limits request size, serves local assets with CSP and records no sequence-bearing request logs. These controls are tested for the initial slice; they are not an ASVS conformance claim.

The application contains no outbound HTTP client, analytics, external font or model integration. Only IDs and view context are kept in localStorage; research data is stored in the local database. OS-level backups and user-selected export destinations remain subject to the user's environment.

Application source license: [Apache-2.0](LICENSE). Unmodified third-party components retain their own licenses, selected license options and source availability in [third-party notices](THIRD_PARTY_NOTICES.md).

Computed-source import: explicitly choose Computed evidence JSON or AlphaFold 3 summary JSON in E. Review actual subjects/model IDs and unmapped fields; inspect/download original submitted JSON in W/R. See the [computed JSON contract](docs/PREDICTION_IMPORT_CONTRACT.md). Independent engineering acceptance8/8+16/16 is registered for0.8; scientific usefulness and complete release acceptance remain separate.
