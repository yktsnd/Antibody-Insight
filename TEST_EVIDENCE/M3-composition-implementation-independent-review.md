# F14/F15 composition implementation: independent review

Verdict: **PASS for F14/F15 and the current complete synthetic J01–J05 engineering paths.** Scientific golden validation, actual researcher evaluation, J06–J08 and Release 1.0 remain **NEEDS-EVIDENCE**.

Reviewer: `/root/observation_review`, independent of product implementation. Finalized 2026-11-04, Asia/Tokyo, after resuming the interrupted review and rechecking the actual saved evidence. Frozen executions are timestamped 2026-11-03 UTC. No broad tests were repeated after resumption because the entire tested source inventory remains unchanged.

Exact tested working-tree source digest: `41a4e108d90a0e35dd0ff1dfcbfc1456b1890a4bc8d723c9c178aed219950623`, in `M3-composition-independent-source-manifest.json`. All73 inventory entries and file digests were independently reverified. Baseline Git commit was `879aad700a4245a6118d4803f275034d52ca2ffe`; the new implementation is not yet committed at this review. Actual-commit registration and preservation of historical artifacts require a separate check.

## Research action and scientific scope

Trace: F14/F15, P05, J05, AC-J05; retained regression J01–J04. I reviewed the charter, original J05/AC, ADR-0008, component/domain/storage/API contracts, changed UI/integration, the earlier independent design/domain reviews and current alignment. No product code was edited by this reviewer; additions were tests and evidence only.

The full J05 replay selects two actual source BindingUnits with paired/single-chain declarations, enters explicit chain identities/roles/copies, source intervals and literal linker sequence, reorders stable parts and reviews source usage before saving. W exposes all saved chain sequences, copies, source IDs and original source molecules. A second composition copies an explicit parent, preserves part IDs/connections, changes the linker and saves exact Lineage. D compares the actual saved design IDs. R retains an annotation-backed proposed question, limits and next experiment. A real process restart and fresh-database JSON reimport preserve all records and graph/order/source identities.

The scientific boundaries are preserved. Source intervals resolve only on their named same-project unit/chain; equal sequence does not collapse identity. Copies and source-chain occurrences describe declarations, not functional units, valency, pairing, chemical validity or physical assembly. Partial use, absent paired chains and differing occurrence counts are visible before saving. Connections retain component endpoints and do not claim individual contacts among repeated chain copies; L11 remains open. Provenance/Lineage DAG validation is separate from permitted declared connection cycles.

Initial compositions have no invented parent. Explicit derivatives require a reason and exact changed signatures. Local researcher notes remain annotation Evidence with null scalar/unit/conditions and actual entry provenance. Hypotheses remain proposed. Source/parent measurements, Constructs/Materials, structures and verified numbering are not inherited. Whole-molecule structure prediction is explicitly unsupported because no validated adapter is registered; no dummy analysis, score or silently broadened source-map scope is used to satisfy the negative case.

## Frozen verification evidence

All executed commands exited zero: Python3.12.10, Chrome156.0.8078.79, pinned local dependencies. Temporary test databases/loopback servers were used. The reviewer personally executed the full Python suite and30 browser checks:

| Command | Result | Fresh preserved evidence |
|---|---|---|
| `pytest -q --tb=short` | 352 passed in66.54s | `M3-composition-independent-python-run.log` |
| `node tests/j01-browser.cjs` | 5 PASS | `M3-composition-independent-J01-results.json` |
| `node tests/j02-browser.cjs` | 4 PASS | `M3-composition-independent-J02-results.json` |
| `node tests/observation-journeys-browser.cjs` | J03three, J04three, public scale one PASS | `M3-composition-independent-{J03,J04,public}-results.json` |
| `node tests/observation-representation-independent-browser.cjs` | 4 PASS | `M3-composition-independent-observation-results.json` |
| `node tests/j05-browser.cjs` | 4 PASS | `M3-composition-independent-J05-results.json` |
| `node tests/composition-independent-browser.cjs` | 6 PASS | `M3-composition-independent-composition-results.json` |

Corresponding independent run logs are retained under the same M3-composition prefix. Named J05 cases are `e2e_j05_bispecific_composition`, `e2e_j05_undefined_chain` and `e2e_j05_unsupported_analysis`, plus the no-outbound/no-JavaScript-error check. J01–J04 retain their exact original main/negative names. These are clearly labelled synthetic engineering fixtures; the separate experimental1MLC check establishes source/scale preservation only.

I inspected all six implementation-agent frozen retained logs: foundation11, numbering5, structural11, previous observation races3, design/hypothesis races4 and save/draft races3, all PASS. They are `M3-composition-final-retained-{browser,numbering-browser,structures-browser,observation-independent-browser,design-hypotheses-independent-browser,design-save-independent-browser}.log`. Combined evidence is **352 Python tests and67 browser checks**. I do not describe those37 additional checks as personally rerun in this stage.

## Independent findings and corrections

Six independently proposed browser groups now pass:

1. A deleted/relabelled component identity cannot be automatically recycled into a dangling connection. The initial implementation reused `part-1` after deletion, allowing an unrelated replacement to acquire the old connection. This was independently reproduced and blocked review. The final draft-local issued-ID registry reserves generated/renamed/deleted IDs and is seeded from parent parts; connection endpoints remain untouched until explicitly repaired.
2. Held review responses are discarded after task/project changes while preserving each draft.
3. A late successful save preserves a newer same-project recipe and its currently selected task.
4. A late save in another project cannot change the active project or erase its unsaved recipe.
5. A rejected old save cannot enable the shared button owned by a newer pending save or inject its error into that newer review. The initial failure is retained as `M3-composition-before-save-error-ownership-independent-failure.json`; exact preview/project/ticket/draft/revision/intent ownership guards fixed it. The injected422 is explicitly a UI fault test; valid imports still use the actual API/storage path.
6. Undefined and declared compositions compare by actual IDs, with declared format/chain role visible and no inferred graph. Copying an undefined composition is disabled.

Independent review also removed the automatic `declared_pairing` default: adding a connection starts with no kind and requires an explicit choice; copied parent kinds retain their actual values. The retained test checks that blank initial state and selects the relationship explicitly.

Seven independent domain/API tests are included in the full suite. They cover repeated/partial/overlapping source instances without union-based functional inference, distinct equal-sequence units, copy imbalance, exact100000 versus100001 assembled-length behavior, stable endpoint ordering/deletion, real session/Origin/CSRF protection, read-only previews/review, atomic rejection of a fabricated measured note, valid/duplicate saves and foreign-source/envelope/provenance spoofing. The combined review API derives its context server-side before saving; supplied fake context fields reject, missing paired usage stays absent and the database remains unchanged.

## Usefulness, gates and remaining work

The established Benchling/HELM benchmark and reuse rationale were independently checked in the design review. The implementation uses native source/part forms, keyboard-accessible ordering and existing graph/identity/persistence mechanisms. D's explicit task controls preserve separate substitution/composition drafts; the saved recipe collapses so comparison remains accessible. The actual comparison screenshot was inspected: source identities, ordered parts, changed linker length, copy imbalance and unsupported-analysis scope are visible. No new renderer, automatic domain recognition, chemistry engine or arbitrary score was introduced. English UI and switchable English/Japanese explanations retain the language policy; retained bilingual checks pass. Actual researcher usability evaluation remains open.

Identity, provenance, local-only confidentiality, reviewed workflow and regression gates: **PASS within this scope**. No unresolved P0/P1 defect was identified in the reviewed implementation. This is not a whole-product zero-defect, performance, ASVS or biological-validity assertion.

After actual-commit/report/hash registration, current synthetic engineering acceptance may be recorded as **J01–J05 5/8 and their prescribed negatives10/16**. Until registration, this report does not invent a commit ID or silently rewrite earlier acceptance. Preserve historical M2/M3-numbered/M3-observation artifacts and the exact new evidence bytes. J06 construct/material comparison, J07 criteria/finalized decision revisions, complete J08 adapters/reproducibility, human scientific goldens, all eight researcher evaluations and final release gates remain open. The next priority is the missing research actions, not additional isolated composition features.
