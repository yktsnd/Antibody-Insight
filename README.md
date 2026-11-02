# Antibody Insight

A local research workspace connecting antibody candidates to sequences, materials, evidence and the reasoning behind a selection.

[日本語の利用ガイド](README.ja.md) · [Product goal](PRODUCT_GOAL.md) · [Development specification](DEVELOPMENT_PLAN.md) · [Current limitations](KNOWN_LIMITATIONS.md)

**Development build: the eight researcher workflows and sixteen prescribed edge cases are not yet complete.** F01–F07 is independently verified, including imported numbering and CDR-H3 observation. This is not Release 1.0. It does not run predictive models or assign antibody numbering automatically.

## Run locally

Requires Python 3.12 or later. The application uses Python's standard library and SQLite; no runtime packages or external services are required.

```powershell
python -m workspace_app.server
```

Open [the local workspace](http://127.0.0.1:8765). To stop, press Ctrl+C in the terminal. Alternatively run `./start.ps1`.

The default database is `%LOCALAPPDATA%/AntibodyInsight/workspace.sqlite3` on Windows, outside this OneDrive checkout. On other platforms it is under `~/.local/share/AntibodyInsight/`. Use `--database PATH --port PORT` to run an isolated workspace. Do not use the development server as a shared or internet-facing service.

## First research action

1. Choose **Import data**. Preview the synthetic example, or import your own FASTA, sequence CSV or awx/1 JSON.
2. Review the valid/excluded rows, sequence repeats, source and target project. Explicitly save the valid records.
3. Select candidates in **E**. Inspect chains and raw sequence positions in **W**. The positions are unaligned indexes, not verified IMGT positions.
4. In **R**, inspect measured/computed labels, source, event time, conditions and the Material → Construct → Molecule path. Record the reason for a shortlist, preview the IDs and evidence, then save a draft.
5. Restart the server and reopen the workspace. Saved records and drafts persist. **Export JSON** creates an explicit local download suitable for reimport into an empty database.

Use **Preview composition fixture** to inspect two explicitly declared binding units, ordered components/linker, chain copy counts and composition lineage in W. Origin IDs and before/after signatures remain intact after restart and reimport. The declaration does not validate physical assembly, chemical connectivity or binding.

Use **Preview numbering fixture** for explicitly synthetic IMGT annotations. W separates raw indexes, imported IMGT coordinates, domain IDs and verification states. E can group complete heavy-chain CDR3 sequences using eligible imported maps; multiple map versions/domains require an explicit choice. Unknown, truncated, unverified and failed maps remain visible. No sequence is sent to a numbering service.

**D** retains the selection context and explicitly identifies pending design operations. The researcher guide in the application switches between English and Japanese. UI labels, code and identifiers use English. Japanese explanations use curated antibody-research terminology.

## Import contracts

- FASTA: one header/sequence record creates one unpaired molecule with `format=unspecified` and `role=unknown`. Pairing, molecular format and biological function are not inferred.
- Sequence CSV: `external_id,name,sequence` are required. Optional columns are `chain_role,format`. This is not the measurement CSV importer.
- Workspace JSON: versioned `awx/1` with strict entity/reference validation. Measured evidence requires a Material ID. Missing values/conditions remain null; zero remains zero. Unknown source version stays null.
- ID collisions reject the entire save. Unknown fields are reported rather than discarded. Entities and draft snapshots are append-only. An existing project can accept new entities only with unchanged project metadata.

See [the data contract](docs/DATA_CONTRACT.md), [explicit composition contract](docs/COMPONENT_CONTRACT.md) and [numbering contract](docs/NUMBERING_CONTRACT.md). Stored component graphs, composition lineage and source-bearing IMGT maps are supported. The initial insertion subset is 111/112 decimal extensions; other legitimate IMGT additions are explicitly unsupported. Structures, interactive assembly, numbered variants, hypotheses, criteria-based final decisions, measurement CSV and AIRR adapters remain pending.

## Verify

Development tests require pytest (MIT). Browser tests require Node.js, Playwright (Apache-2.0) and installed Chrome. These are test dependencies only.

```powershell
python -m pytest -q
node tests/browser.cjs
node tests/numbering-browser.cjs
python scripts/check_traceability.py
```

If Playwright is supplied by a separate runtime, set `NODE_PATH` to that runtime's `node_modules` directory. `PYTHON` can select the Python executable and `PLAYWRIGHT_CHANNEL` can select an installed Playwright browser channel. The browser test creates temporary databases and runs its own loopback servers. It does not access the user's research database.

The initial browser suite verifies import preview/QC, 800 records, five selections across E/W/D/R, selected-candidate focus, null versus zero, evidence snapshots, a real process restart, JSON roundtrip, hostile text escaping, no outbound browser requests, a mobile viewport and bilingual explanations. These checks are partial-path evidence and must not be counted as final 8/8 or 16/16 acceptance.

The numbering suite uses 800 synthetic candidates to verify CDR-H3 grouping, chain-specific insertion coordinates, explicit ambiguous-map selection, unavailable/partial/unverified states, map-choice restart persistence and ID-only group-filter storage. Engineering fixture success is not human scientific validation.

See [test evidence](TEST_EVIDENCE/README.md), [traceability](TRACEABILITY.csv), [the initial review](docs/INITIAL_REVIEW.md) and [the acceptance plan](docs/ACCEPTANCE.md). Human-validated scientific golden fixtures and researcher evaluations remain outstanding.

## Architecture

`web/` owns the four-screen UI and local selection state. `workspace_app/domain.py` owns identity/provenance constraints, `storage.py` owns SQLite transactions, and `adapters.py` owns input formats. The loopback API validates Host, Origin, session and CSRF token, limits request size, serves local assets with CSP and records no sequence-bearing request logs. These controls are tested for the initial slice; they are not an ASVS conformance claim.

The application contains no outbound HTTP client, analytics, external font or model integration. Only IDs and view context are kept in localStorage; research data is stored in the local database. OS-level backups and user-selected export destinations remain subject to the user's environment.

License: [Apache-2.0](LICENSE).
