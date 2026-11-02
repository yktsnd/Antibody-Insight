# Initial M1 slice: independent implementation review

Verdict: **PASS for F01–F05 only**.
Full M1 milestone: **NEEDS-EVIDENCE**.
J01–J08 and Release 1.0: **NEEDS-EVIDENCE**; this report does not claim 8/8 main flows or 16/16 specified negatives.

Reviewer: `/root/independent_review`, separate from the implementation agent.
Date: 2026-11-02, Asia/Tokyo; final independent browser execution completed at 2026-11-02T14:35:24.974Z.
Repository base: `0fa83529cb04dfc3128730b8997d91c058424e1d`; implementation was an uncommitted worktree during review. Exact reviewed source hashes are retained in TEST_EVIDENCE/M1-source-manifest.json (source-set digest `1e03a6c3ea07c3503a48da4fa2c8ba87d1676e8b7ec7b6cf62ba1d7473ded8da`).

## Scope and review method

Traceability: P01/P06/P07/P08; J01/J06/J07/J08; AC-J01/AC-J06/AC-J07/AC-J08, limited to the declared F01–F05 foundation slices in docs/ACCEPTANCE.md.
Reviewed: workspace_app/*.py, web/app.js, web/index.html, web/style.css, tests/test_foundation.py, tests/browser.cjs, docs/DATA_CONTRACT.md and the governing product/plan/AC/ADR material reviewed in M0.
Reviewer added tests/test_independent_review.py and this report, without modifying product code.

The implemented action is local import preview → explicit save → sequence/chain observation with retained selection → provenance inspection → immutable shortlist draft → restart/export/reimport. The data are persisted in SQLite. Tests use explicitly synthetic engineering fixtures and isolated temporary databases. No numbering, biological alignment, structure correspondence, scientific score or prediction is calculated.

The reviewer independently reran the domain/HTTP suite and the actual Chrome browser suite after corrections. The browser suite was inspected before running; it starts its own server/database, restarts the server, downloads JSON and imports it into a fresh database. Screenshots alone were not used as persistence or scientific correctness evidence.

## Executed evidence

1. `python -m pytest -q`: **55 passed in 7.66s**, exit code 0. This includes 12 independently added cases and preserves the implementation tests. Recorded in TEST_EVIDENCE/M1-independent-test-log.txt.
2. PowerShell browser replay:

   ```powershell
   $env:NODE_PATH='C:\Users\yukis\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
   node tests/browser.cjs
   ```

   Result: **10 checks PASS**, exit code 0, Chrome `156.0.8078.79`.
3. TEST_EVIDENCE/M1-browser-results.json contains the final independent browser replay result and dataset SHA-256 `9e5ffeb37eb956dfe8c4a6d81cbba2c82adcad838cee854e3fa445f69bceab98`.
4. TEST_EVIDENCE/M1-evidence-screen.png and M1-mobile.png were visually inspected. Five selected candidates, measured/computed distinction, zero/missing/unknown conditions, source paths, synthetic labels and draft status are readable. The mobile layout fits the tested viewport. M1-explorer-800.png records the 800-candidate view. These are supporting UI evidence, not independent scientific validation.

## Acceptance replay for the declared slice

| Slice | Result | Independently confirmed |
|---|---|---|
| F01 | PASS | 800 FASTA candidates retain distinct IDs; duplicates/QC are visible; invalid rows are shown before explicit valid-subset save; JSON/sequence CSV contracts reject malformed/unsupported input; preview does not persist |
| F02 | PASS | E/W retain selection and sequence index; raw indexes are labeled as unaligned and unnumbered; clicking selected candidate 5 opens that candidate; unavailable structure/numbering remains explicit |
| F03 | PASS | Five candidate IDs, reason and complete evidence snapshots save as draft, survive real server restart and can restore selection; empty reasons, unknown/duplicate IDs and unrelated evidence reject; direct UPDATE/DELETE is blocked |
| F04 | PASS | Same protein/different constructs and lots remain separate; measured evidence directly targets Material; source/version/event time/conditions/unit survive; computed is separate; zero and null remain distinct; wrong-type, unknown and cross-project subjects reject |
| F05 | PASS | Fresh export is loaded from current DB; empty-DB JSON reimport preserves identities/content and snapshots; ID collisions and project changes reject atomically; unknown fields and unsupported structure input do not alter existing data |

## Independent findings and correction verification

All issues below were reported before integration and corrected by the implementation agent. No unresolved P0/P1 issue was found in the reviewed initial slice after correction and replay.

| Finding | Reproduction and consequence | Verified correction |
|---|---|---|
| Snapshot numeric-type tampering | Python equality accepted an imported frozen measurement changed from `0.0` to `False`; nested condition `0` to `False` also compared equal | Snapshot is separately validated and compared using canonical JSON, so both cases reject without writes |
| Focused selected candidate absent | With five selected, opening candidate 5 displayed the first two selected candidates | Focus is displayed first while keeping all selection IDs; actual browser assertion verifies candidate 5 and breadcrumb |
| Huge integer request disconnect | `10**400` raised uncaught OverflowError in numeric validation instead of HTTP 422 | Numeric validation rejects unsupported range with HTTP 422 in values and nested conditions; no DB changes |
| Browser integer rounding | Integer `2**53+1` could be accepted by Python and rounded during browser JSON processing | Explicit documented interoperable integer range rejects it before persistence; values and conditions tested |
| Float underflow | JSON `1e-999` parsed as zero, altering a nonzero input silently | JSON float parser rejects nonzero underflow/overflow; actual zero remains valid |
| Reference-order exception | A Decision before a Material with a dangling Construct caused KeyError during ownership resolution | Missing/wrong Construct raises ValidationError and leaves the database empty; valid reversed-order graphs still roundtrip |

The reviewer proposed and executed additional cases beyond the implementation happy path: exact JSON-type snapshot equality, nested boolean tampering, reversed forward references, decision-before-invalid-material, unknown source version with hostile text, missing nested version and multiple unknown source keys, underflow versus true zero, authenticated cross-site GET rejection, duplicate JSON keys/invalid UTF-8, and four large-integer field/range combinations.

## Mandatory gates and limits

- **Identity PASS for this slice:** no sequence-based molecular merge; typed IDs and validated project/type references; independent constructs/materials persist. Molecular component graphs, BindingUnit and Lineage remain pending. A simple chain list does not satisfy complete molecular assembly or the full M1 lineage/composition gate.
- **Provenance PASS for this slice:** immutable typed Evidence, exact snapshots, explicit sample ownership, source version or honest null, timestamps and unknown conditions. No child measurement inheritance feature is implemented or claimed.
- **Security PASS for this local development slice:** loopback-only binding, Host/Origin/session/CSRF checks, request-size/type validation, CSP, no-store responses, output escaping and no sensitive request logging were inspected and relevant rejection cases executed. Hostile imported HTML remains text; the browser recorded no external requests or JavaScript errors. This is not an ASVS compliance claim, shared-user authentication review, or comprehensive OS-level network/permission audit.
- **Regression PASS for this slice:** all current tests pass after corrections. The test suite is preserved. The eight final research journeys do not yet exist as completed executable flows.

KNOWN_LIMITATIONS L01–L10 remain in force: human-verified scientific golden fixtures, verified numbering/structures, molecular graph/lineage/design, hypotheses, measurement CSV/comparison, finalized decisions/revisions, final exchange adapters, researcher evaluation, performance/coverage/full E2E gates and shared-user deployment remain open. No clinical or predictive-validity claim is supported by these engineering tests.

Integration may record this initial-slice PASS only. Keep full journey statuses incomplete and attach the actual integration revision and source manifest to TRACEABILITY/evidence; further domain changes require another independent review.
