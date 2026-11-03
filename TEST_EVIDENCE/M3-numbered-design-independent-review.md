# F10/F11 numbered designs and hypotheses: independent implementation review

F10 implementation: **PASS**.
F11 implementation: **PASS** within the shared proposed-hypothesis scope.
Full synthetic-fixture J02 engineering path and its two prescribed negatives: **PASS**.
Current-source full synthetic J01 regression: **PASS**.
Scientific-UX and mission alignment for this action: **PASS**.
Complete M3, full J03/J04/J05/J06, scientific/user validation and Release 1.0: **NEEDS-EVIDENCE**.

Reviewer: `/root/j01_replay_review`, separate from implementation; no product code edited by this reviewer.
Date: 2026-11-03, Asia/Tokyo. Baseline: `9bc23c781cc046254c993ad953f3addff5fd22b6` plus reviewed working-tree implementation.
Exact final tested source: `TEST_EVIDENCE/M3-numbered-design-independent-source-manifest.json`, source digest `0a83537619e862d351b949fb02424038ddb9ff653022eac19876d367330235c5`.
The complete source inventory and every digest were checked after the final replay and remained unchanged. Subsequent documentation/acceptance registration does not authorize runtime changes without fresh evidence.

## Action, authority and scope

F10 traces P02/P04 → J02/J04 → AC-J02/AC-J04. F11 traces P02/P03/P04/P06 → J02/J03/J04/J06 and their ACs. Shared plumbing does not pass those other complete journeys.

The researcher selects a parent and explicit source numbering map, inspects an optional supplied reference, chooses exact substitutions, previews a new child and full Lineage, then saves a distinct proposed Hypothesis with original evidence, limitations and next experiment. The J02 fixture includes parent VH/VL and explicitly labelled synthetic reference layout. No biological human-reference validity is claimed.

Inputs are existing immutable Molecules, ResidueMaps, Evidence, declared components and Structures. Outputs are new Molecule/Lineage/Hypothesis records. Preview writes nothing; explicit save/import atomically validates the complete graph. No parent measured record, construct, material, structure, correspondence or numbering attestation is inherited. Automatic humanization, predictive scores, new numbering, indels, interactive assembly, construct comparison and finalized decisions remain outside this action.

The reviewer revisited PRODUCT_GOAL, DEVELOPMENT_PLAN and the original J02/AC-J02 plus shared J03/J04 requirements; AGENTS and the requester quality constraints; traceability; ADR-0006; DESIGN_CONTRACT; SCIENTIFIC_UX; the independent design review; current limitations/progress; and the implementation/tests. Inspection covered design.py, hypotheses.py, composition/domain/server integration, design_fixtures.py, web/design.js, app.js/structures.js/index/style integration and browser/acceptance evidence. The reviewer added twelve domain cases and two browser suites. The work addresses a required missing research action; a discretionary feature score does not replace the mandatory gates.

## Final independent execution

All commands below ran sequentially against the frozen final source and exited 0. Python was the workspace `.venv/Scripts/python.exe`; NODE_PATH selected the bundled Playwright runtime. Chrome was `156.0.8078.79`. Full output is retained in `M3-numbered-design-independent-test.log`.

| Command | Observed result |
|---|---|
| `.venv/Scripts/python.exe -m pytest -q --tb=short` | **297 passed in 27.03s**, including twelve independent M3 domain cases |
| `node tests/browser.cjs` | **11 checks PASS** |
| `node tests/numbering-browser.cjs` | **5 checks PASS** |
| `node tests/structures-browser.cjs` | **11 checks PASS**, including actual canvas selection, rotation and zoom |
| `node tests/j01-browser.cjs` | **5 checks PASS**, including complete main path and both prescribed negatives |
| `node tests/j02-browser.cjs` | **4 checks PASS**, including complete main path and both prescribed negatives |
| `node tests/observation-independent-browser.cjs` | **3 checks PASS** |
| `node tests/design-hypotheses-independent-browser.cjs` | **4 checks PASS** |
| `node tests/design-save-independent-browser.cjs` | **3 checks PASS** |

Total: **297 Python tests and 46 browser checks**. Fresh independently named complete journey reports are `M3-numbered-design-independent-J01-results.json` and `M3-numbered-design-independent-J02-results.json`; both identify the reviewer and shared source manifest. The retained M2 independent J01 report/manifest were preserved. The earlier broad replay preceding the newly found save defect is separately retained as `M3-numbered-design-before-save-fix-test.log` and its source manifest; it is not final acceptance evidence.

The pre-registration traceability checker intentionally exited 1 because the current row still referenced M2's old source inventory. Its diagnostic was `Source inventory changed; independent replay required`, retained in `M3-numbered-design-pre-registration-traceability.log`. This correctly blocks stale current acceptance; it is not reported as an application regression or checker PASS. These new results authorize fresh J01/J02 registration after recording the actual implementation commit. Root must then rerun the checker against those records. Expected engineering counts after valid registration are **2/8** journeys and **4/16** prescribed negatives, with all scientific/user/final integration gates still separate.

## J02 acceptance replay

| Requirement / named case | Independent result |
|---|---|
| `e2e_j02_humanize_variant` | PASS: explicit parent VH/VL and supplied reference imported; W selects source H111.1/CDR3; D displays parent/reference coordinates and stages H111.1 plus L10/FR1; full before/after child and Lineage preview writes nothing; explicit save preserves every original record |
| Exact mutation identity | PASS: saved changes retain parent map, chain/domain/scheme, integer/insertion pair, actual raw index and original/target residue; parent H111.1 remains N while child becomes P; parent L10 remains M while child becomes V |
| Child evidence boundary | PASS: new child has no inherited material/construct/evidence/structure/map; W explicitly shows child numbering unavailable; D labels regions as parent-source scope |
| Retained reasoning | PASS: R saves proposed text, next experiment, limitations, actual parent Material Evidence ID, Lineage and child raw residue; Hypothesis remains distinct from measured/computed evidence and shortlist drafts |
| Persistence/reuse | PASS: actual process restart restores exact exported entities/context; fresh database JSON import equals the saved bundle, including original records, child, complete Lineage and Hypothesis |
| `e2e_j02_numbering_unavailable` | PASS: exact unavailable map is natively disabled; actual keyboard ArrowDown cannot choose it; direct preview rejects 422 and the database remains exactly unchanged |
| `e2e_j02_insertion_mapping` | PASS: 111 and 111.1 stage separate raw indexes; absent 111.2 has no editable row, rejects directly without a neighbour fallback, and changes no stored data |

The complete current-source J01 path also passes with 800 accepted candidates, QC/excluded rows and repeats, imported CDR-H3 grouping, explicit observation context/material choice, two-candidate observation, five IDs and reason/source snapshots, and actual restart. Neither the new design UI nor compact counts changed those identities or numeric semantics.

## Independent cases, defects and correction

Twelve independently added domain cases cover cross-component boundaries on a two-copy chain; preservation of unrelated component origins/connections/copies; six tampered-child/partial-save imports; two maps with different coordinate labels resolving to one physical raw residue; Hypothesis model/correspondence isolation; parent Evidence/Lineage scope; sequence reversion without invented BindingUnit ancestry; and genuine unknown-model CIF context remaining null while invented model 1 rejects.

Three implementation defects were independently reproduced and corrected before this verdict:

1. **Wrong-model correspondence accepted in a Hypothesis.** The original validator checked that the model existed and the map named the same Structure, but accepted model 1 with a map covering only model 2. It now requires the chosen correspondence to cover the actual selected source model. The independent domain regression rejects that combination atomically and still accepts a genuine unknown source model without inventing model 1.
2. **Old hypothesis preview reopened over a new scope.** Holding a preview response, closing the dialog, selecting another candidate and reopening a blank proposal allowed the old response to display. Separate hypothesis-dialog/request generations now guard success, error and busy-state cleanup; close/reopen/project changes invalidate older work. The independent browser releases the old response only after the new scope is open and verifies no old preview/text replaces it. Project-scoped memory drafts stay outside localStorage, and a variant reason edited during its pending preview causes that preview to reject until freshly reviewed.
3. **Old save completion erased a new draft.** Holding a first parent's import, closing its preview and staging another parent's mutation caused the old callback to clear the current draft. The fix captures the submitted draft object/revision, Hypothesis key/text/session and preview ownership. It clears only unchanged submitted data, closes only its own dialogs, and changes selection/Lineage only for the same operation context. Three actual browser cases verify different-parent mutation preservation, newer same-parent mutation/reason preservation, and a newer Hypothesis dialog/text/question surviving an old save and subsequent reopen. Late cleanup cannot enable another preview's save control.

The first full regression run passed but did not cover defect 3; it was preserved, the new reproducer added, and the entire suite replayed after correction. No previously passed run was relabelled as covering that defect.

Two harness issues were separated from product defects. Playwright's disabled helper retargets an OPTION inside a wrapping LABEL to the enabled SELECT. The reviewer independently reproduced labelled `isDisabled=false` with native option.disabled=true, while an unlabelled option returned true. The corrected J02 test retains native disabled/:disabled assertions, real keyboard rejection, API 422 and exact unchanged data; no product validation was relaxed. Separately, the save harness's dynamic `:checked` locator stopped identifying a checkbox after rerender; capturing its stable data-select ID corrected that harness without changing its assertions. See M3-J02-harness-investigation.md.

## Scientific identity, confidentiality and regression gates

Identity/provenance: **PASS in scope**. Backend resolution uses actual parent map/molecule/chain/raw residue; overlapping aliases cannot authorize two edits to one raw locus. Eligible partial maps authorize observed positions only. Reference comparison retains sources, gaps, region counts and incomplete coverage, without inferring homology, human species or deletion. Exact insertion strings are preserved. Full reconstruction rejects hidden changes to unrelated chains, roles, copy counts, format or origins. Changed component origins become unavailable only where exact source intervals no longer match; full parent signatures and Lineage retain ancestry, including declared copy effects. Equality after reversion does not reconstruct an origin.

Hypotheses remain proposed, immutable, source/time-bearing local entries. Original evidence stays on its direct subject; Lineage requires both parent and child in scope, and residue/model/map contexts resolve on actual named records. No authenticated author, validation, score, child experiment or confidence is fabricated.

Confidentiality: **PASS for the inspected local implementation and tested controls**. Existing loopback/session/Origin/CSRF/CSP and atomic persistence mechanisms are reused. No new service/dependency is introduced. Mutation and scientific-text drafts stay in memory; accepted UI context stores IDs, not new sequences or unsubmitted research text. Monitored complete and independent browser suites observed no outbound requests or JavaScript errors. This is not a comprehensive endpoint/OS audit, ASVS certification or final deployment-security gate.

Regression: **PASS**. All retained tests and real browser flows pass on the exact final source. The obsolete assertion that D was wholly unimplemented was replaced by its actual new heading while retaining the same five-ID context assertion. Existing scientific/data assertions were retained. No unresolved P0/P1 defect was identified within this reviewed scope; that statement does not assess unimplemented journeys.

## Scientific UX and mission assessment

**PASS for the implemented action.** The independently checked primary-document comparison uses Jalview and IMGT for D/E, Mol* and Jalview for W, and eLabFTW and Jalview for R. The previously inaccessible Jalview tutorial is corroborated by its official HTML feature/format documentation. These are documentation benchmarks, not claimed hands-on research-user tests. Sources and reuse reasoning are recorded in SCIENTIFIC_UX.md and M3-design-independent-review.md, including [IMGT's equal-CDR-length caveat](https://www.imgt.org/IMGTScientificChart/Numbering/IMGTnumbering.html).

The implementation reuses native controls, imported numbering, existing local structure/source views and atomic preview/import. The narrow coordinate table exposes exact parent/reference residues, original map details, observed region counts/coverage, staged changes and source-scoped differences. Parent labels do not attest to child numbering. The single primary R hypothesis action was moved above potentially long evidence lists; original evidence remains accessible. E's decorative count cards became one compact line preserving the same counts/IDs. These small changes directly support the explicit density/findability requirement; they do not introduce a new dashboard, editor framework, unsupported score or new workflow.

The useful result is a reproducible child design and proposed experiment with original reasons/sources. Control counts and 297 test passes do not establish biochemical success or researcher usefulness. J02 is verified with explicitly labelled engineering fixtures, not human-validated antibodies or actual humanization experiments.

The next gap is completing the own named J03/J04 paths through this shared functionality, followed by J05's explicit interactive composition and M4's construct/material comparisons and finalized decisions. Avoid further isolated controls, prediction engines or incidental polish ahead of those actions. Complete M3 still requires its remaining journey gates. Human-validated scientific goldens, real researcher evaluation, full J08 adapters/roundtrip, final coverage/performance/storage/security measurements, all eight restart paths and final 8/8 + 16/16 review remain pending.

This PASS authorizes integration of the exact reviewed F10/F11 implementation with fresh acceptance bookkeeping. It does not complete M3 or Release 1.0.
