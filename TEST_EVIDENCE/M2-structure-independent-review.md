# F08 explicit structural observation: independent implementation review

F08 implementation: **PASS**.
Full M2, complete J01–J08 and Release 1.0: **NEEDS-EVIDENCE**.

Reviewer: `/root/independent_review`, separate from the implementation agent.
Date: 2026-11-03, Asia/Tokyo.
Baseline: `d6d0748897048ce759a4191f1140c05b58e990db` plus reviewed F08 worktree changes.
Final reviewed source set: TEST_EVIDENCE/M2-F08-independent-source-manifest.json, digest `5cbc6727141f8fc2d09b6dcfd1a7c714509b3b4f2a706a114f5f54e1016fc72e`.

## Scope and review method

P03/P04/P08 → J03/J04/J08 → AC-J03/AC-J04/AC-J08, F08 only, retaining F01–F07 regressions.
The reviewer inspected structures.py, domain/adapters/server changes, structural fixtures, StructureUI/app integration, parser tests and all three browser suites against ADR-0004 and the clarified STRUCTURE_CONTRACT. Primary definitions/dependency licenses were checked in M2-structure-design-review.md. The reviewer added tests/test_structures_independent.py and review evidence, without changing product code.

The tested action is local PDB/mmCIF preview/import with a declared primary Molecule → explicit model/map/chain/residue observation → actual rendered-canvas and sequence selection → linked orientation/zoom → computed evidence inspection → immutable map creation → restart/export/reimport. Tests use synthetic engineering coordinates, not human-validated biological structures or predictions.

## Independent executions

| Execution | Observed result |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest -q` | **207 passed in 23.78s**, exit 0; includes 23 independent F08 cases |
| `node tests/browser.cjs` | **11 checks PASS**, exit 0 |
| `node tests/numbering-browser.cjs` | **5 checks PASS**, exit 0 |
| `node tests/structures-browser.cjs` | **11 checks PASS**, exit 0, including physical mouse clicks/rotation/wheel zoom |
| `.\.venv\Scripts\python.exe scripts/check_traceability.py` | **PASS**: eight journey definitions/eight implementation slices; full journey acceptance remains **0/8**, prescribed final browser negatives **0/16** |

Browser runs used the pinned local Python environment, existing bundled Playwright runtime and installed Chrome `156.0.8078.79`. All three browser suites were run sequentially. Detailed reports are M1-browser-results.json (`2026-11-02T22:14:14.405Z`), M2-numbering-browser-results.json (`22:15:32.518Z`) and M2-structure-browser-results.json (`22:18:49.935Z`); these timestamps are 2026-11-03 JST. No artifact-write failure occurred in this final replay. Commands and observed output are retained in M2-structure-independent-test-log.txt.

The Python suite preceded the final small Link-checkbox feedback/CSS layout correction. Those UI changes were separately inspected and exercised by the final F08 browser replay, including both checked boxes. No domain behavior changed afterward. README/runtime/dependency instructions were also updated and inspected; these documentation changes do not expand the scientific claims.

M2-structure-screen.png was visually inspected after the final run. Both source panels, actual atom rendering, checked Link controls, non-overflowing correspondence controls, declared antigen references, synthetic labels, source/parser/version and distinct scoped/missing confidence are visible. The screenshot supports UI review; persisted-data assertions and physical interaction establish the behavior.

## F08 acceptance replay

| Requirement | Verdict | Independent evidence |
|---|---|---|
| Preserve local coordinate source | PASS | Exact UTF-8 text/digest and immutable Structure/Map IDs survive restart and fresh-DB JSON roundtrip; corrupt/digest-mismatched imports leave existing data unchanged |
| Full source identity | PASS | Model, author/label chain and sequence identifiers, segment, insertion, residue name and explicit conformers remain distinct; negative/zero author numbers, quoted identifiers and unknown fields retain their meanings |
| No parser-generated science | PASS | No entity/subchain/label-sequence assignment or first-conformer helper is called; absent occupancy/B remain null; missing CIF model stays explicitly unknown and viewable without model-1 correspondence or model-scoped score |
| Explicit correspondence | PASS | Valid assigned antibody-chain/standard-AA mapping works; same source locus cannot map to two sequence positions through alternates or microheterogeneity; actual cross-project same-sequence ownership fails |
| Physical reciprocal selection | PASS | Actual PDB H3A and L1 canvas clicks and mmCIF author/label-distinct click select the exact sequence position; sequence selection highlights the exact mapped atoms; missing positions/unmapped alternate B select no substitute |
| Explicit comparison view | PASS | Physical rotation and wheel zoom synchronize orientation/zoom; each original center stays unchanged and distinct; linked views remain consistent after a source-model switch and restore after restart |
| Evidence meaning | PASS | Structure remains the direct computed-evidence subject; measured Structure evidence rejects independently of metric name; model 1/model 2 scores differ correctly; absent confidence is not inferred from source B values; unknown score scope remains file-level/unspecified |
| Editable declarations without overwrite | PASS | Raw PDB import requires an explicit primary Molecule; manual GUI chain/residue pairing validates, exposes a bad preview, then saves a new immutable map; old maps/source/evidence remain unchanged |
| State/security/regression | PASS within tested local scope | Newly appended evidence refreshes W, project views remain isolated, saved state holds IDs/camera context rather than coordinate files; all previous tests and browser actions pass with no outbound requests or JavaScript errors |

## Independent boundary cases

The 23 independently added cases cover eight quoted CIF numeric-marker combinations; quoted literal versus unknown/blank identifier codes; omitted and mixed unknown/known models; unknown versus blank segments; two zero/negative author-number cases; conformer and residue-name/microheterogeneity locus duplication; two preserved score-scope/missing-value cases; measured Structure subject rejection; actual cross-project same-sequence primary ownership; exactly **100,000** atoms versus **100,001**; and negative/positive TER-boundary cases.

The 100,000-atom case verifies parser preservation/capacity and explicit over-limit rejection. It does not establish WebGL performance or final hardware latency at that capacity. The supplied browser fixtures are deliberately small for deterministic source-key and physical-click verification.

## Findings corrected before PASS

1. **Quoted CIF numeric null markers were silently treated as missing.** Decoding quoted `'.'`/`'?'` and then applying generic optional-number handling erased the distinction between literals and CIF missing markers. Source-token checks now reject the quoted numeric literals while retaining genuine nulls and quoted identifier codes.
2. **Unknown source fields were defaulted.** CIF segment unknown/missing had collapsed to blank and an omitted model column had become model 1. Unknown fields now remain null. The clarified adapter permits an unknown-model view but prevents explicit-model mapping/editor/scoped scores. Mixed unknown/positive models have deterministic ordering.
3. **Explicit atom limit errors were hidden.** ValidationError inherited ValueError and the broad CIF parser catch replaced the 100,000 limit diagnostic with generic syntax failure. Domain validation errors now retain their intended diagnosis.
4. **TER-separated residue identity could merge.** Different atom names at an identical source locus before/after TER were initially merged into one residue. Reused source loci across chain parts now reject. A first over-broad chain guard was refined so normal post-TER water/ligand residues with distinct numbers remain viewable; both cases pass independently.
5. **Appended confidence remained stale in W.** Derived StructureUI responses were cached across bundle reloads. Cache invalidation now tracks the current bundle, and an actual import/appended-model-score/browser case shows the new value without stale missing-confidence output.
6. **Old project camera state could enter a new project.** Disposal previously occurred after replacing global state. Existing viewers are now disposed and remembered before project replacement; the actual project-switch browser case verifies empty structural state in the new project and restored state in the original.
7. **Visual feedback/layout issues.** Implementation visual QA identified a global Link state with an unchecked peer checkbox and long correspondence text overflowing its grid cell. Final controls synchronize and the grid constrains its children; the final browser assertion and inspected screenshot verify the corrections.

No unresolved P0/P1 issue was identified within F08 after correction and replay. This is not a claim of zero defects in unimplemented journeys.

## Regression, dependency and scientific limits

The pre-existing corrupt-structure test was retained. Its former unsupported-PDB expectation became obsolete when PDB support was added; it now supplies valid explicit import context and exercises actual malformed PDB, preserving the unchanged-database assertion. No test was removed to manufacture success.

Gemmi **0.7.5** is an unmodified external MPL-2.0 dependency; locally served 3Dmol **2.5.5** retains BSD-3-Clause and bundled notices with GLmol's MIT option selected. Local vendor hashes match the recorded manifest. Application licensing remains Apache-2.0. Runtime geometry/model data remain local; no CDN or remote structure/model request was observed. This is an implementation check of the declared dependency boundary and tested local controls, not a comprehensive ASVS, distribution-law or dependency-security certification.

Author/label keys and conformers are source metadata, not automatic molecular identification. Antibody/antigen roles and target references are explicit declarations. Only the supported standard residues are sequence-mappable; unknown/modified residues stay unmappable. A shared camera is expressly not structural superposition, and viewer display geometry is not evidence of chemical connectivity, secondary structure or biological assembly. Supplied AlphaFold-named metrics remain model-internal computed values; no affinity, prediction accuracy or success threshold is invented.

Full M2 and the eight complete journeys remain pending, including the remaining required end-to-end observation/selection work and later saved hypotheses/design/decision steps. Human-validated scientific golden fixtures, researcher evaluation, complete cross-format acceptance, final branch coverage, standard-hardware performance/storage/security gates and final independent journey replay are not passed by these engineering tests.

F08 may integrate with the exact reviewed revision and evidence recorded. Further domain changes require independent review.
