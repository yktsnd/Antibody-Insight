# F09, J01 and M2: independent implementation review

F09 contextual numeric ordering: **PASS**.
Full J01 engineering acceptance, using clearly labelled synthetic fixtures: **PASS**.
M2 engineering milestone (J01/J03 foundation paths, retained selection, numbering/structure negatives): **PASS**.
Complete J02–J08 and Release 1.0: **NEEDS-EVIDENCE**.

Reviewer: `/root/j01_replay_review`, independent of the implementation agent, with fresh review context.
Date: 2026-11-03, Asia/Tokyo.
Exact tested source: `TEST_EVIDENCE/M2-observation-independent-source-manifest.json`, source digest `1ac9421ff8b7c4d852e3b9e5cbc60332a86053face3a3dea4d5361f3fc82652d`.

## Scope and authority

Primary trace: P01 / J01 / AC-J01 / F09. Shared ordering boundaries also concern P04/P06/P07, J04/J06/J07 and their ACs; their full paths are not passed here. Retained F07/F08 foundations cover the original M2 numbering/structural-observation gate, including J03 foundations. Full J03 hypothesis/design remains later M3 work.

The reviewer read AGENTS.md, PRODUCT_GOAL.md, DEVELOPMENT_PLAN.md (J01 and AC-J01), TRACEABILITY.csv, ADR-0005, OBSERVATION_CONTRACT, the independent design review, current limitations, and the prior F07/F08 reviews. The reviewer inspected observation.py, discovery_fixtures.py, domain validation and direct subject resolution, new-project data_class handling, server/API integration, app.js, J01/browser tests, check_traceability.py, record_evidence.py and acceptance-verifier tests. Only independent tests and review evidence were added by this reviewer; no product code was edited.

User action: preview/import 800 accepted candidate sequences, inspect excluded rows and repeats, group imported CDR-H3, explicitly choose a binding observation context and a multiple-material observation, compare two candidates in W, select five IDs in E, save their reason and evidence in R, then restart the actual server and restore them.

Inputs are labelled synthetic CSV sequences plus an explicit supplementary numbering/Material/Evidence JSON referencing the real imported IDs. Outputs are an ordering/view and an immutable shortlist draft. Affected entities retain separate Project, Molecule, chain, Construct, Material, Evidence and Decision identities. There is no aggregation, unit conversion, candidate-success prediction, new scientific score, automatic VH/VL pairing, final weighted decision, design mutation or proprietary-data transmission in this scope. This is required J01 work rather than a discretionary feature.

## Independent execution

All final commands ran sequentially against the frozen source and exited 0. The full output is retained in `TEST_EVIDENCE/M2-observation-independent-test.log`.

| Command | Observed result |
|---|---|
| `.venv/Scripts/python.exe -m pytest -q --tb=short` | 252 passed in 35.48s; includes six new independent observation cases and eleven acceptance-verifier cases |
| `node tests/browser.cjs` | 11 checks PASS |
| `node tests/numbering-browser.cjs` | 5 checks PASS |
| `node tests/structures-browser.cjs` | 11 checks PASS; physical canvas clicks/rotation/zoom retained |
| `node tests/j01-browser.cjs` | 5 checks PASS; all five main-path steps executed, including a real process restart |
| `node tests/observation-independent-browser.cjs` | 3 independent race/security checks PASS |
| `.venv/Scripts/python.exe scripts/check_traceability.py` | PASS: eight journey definitions, nine implementation slices; still 0/8 and 0/16 before this review is registered |

Browser runs used the pinned local Python environment, the bundled Playwright runtime via NODE_PATH, and installed Chrome `156.0.8078.79`. PYTHON pointed to the workspace `.venv/Scripts/python.exe`. The independent J01 result is stored in `TEST_EVIDENCE/M2-observation-independent-J01-results.json`; the source browser report is `J01-browser-results.json`. Retained reports are M1-browser-results.json, M2-numbering-browser-results.json and M2-structure-browser-results.json. Independent race results are M2-observation-independent-browser-results.json. Screenshots supplement these persisted-data and interaction assertions.

## J01 acceptance replay

| Requirement / named test | Verdict and evidence |
|---|---|
| `e2e_j01_candidate_shortlist` | PASS: 802 CSV input rows previewed; exactly 800 valid, distinct candidates saved; repeated sequences are labelled rather than merged; original imported chain IDs used for explicit supplementary fixture data |
| CDR-H3 and binding observation | PASS: exact imported CDR3 grouping, ascending/descending numeric ordering, original condition details, real zero, distinct units, unknown conditions, and explicit alternate-Material Evidence selection exercised |
| Two candidate observation | PASS: W opens two different selected candidates, displays their sequence differences, and clicks differing CDR3 residues with raw-index/imported-IMGT labels |
| Five IDs, reason and provenance | PASS: E retains five IDs into R; preview includes actual chosen Evidence ID; saved draft includes exact IDs/reason and complete original evidence snapshots |
| Persistence | PASS: actual server process stopped/restarted at the same origin; exported bundle exactly equals saved bundle; five IDs, reason, evidence snapshots, selected cohort and explicit observation restored |
| `e2e_j01_invalid_sequence` | PASS: missing-sequence and invalid-symbol rows are visibly excluded, preview writes nothing, and explicit valid-subset confirmation saves 800 rather than 802 |
| `e2e_j01_missing_measurement` | PASS: registered null is not zero; true zero remains numeric; incomplete context, different unit/context and no measurement retain separate statuses; R shows missing and zero distinctly |
| Language and confidentiality | PASS: English/Japanese guide switching preserves localStorage context and exact exported data; curated humanness/humanization wording remains distinct; no outbound browser requests or JavaScript errors in the replay |

## Independently proposed and added boundaries

1. **Old cohort identity after a new representative and reordered reimport.** Add an Evidence ID sorting before the original representative, reverse entity order, persist and reopen the database. The original cohort-member ID still defines the same context, explicit original observation stays zero, and the result is identical. This passes in test_original_cohort_member_survives_earlier_representative_and_reimport.
2. **Explicit null versus another lot and the same protein sequence.** Add a null observation from another Material and a finite negative value. Choosing null keeps its exact Evidence ID and missing state in both directions, with all unavailable values after numbers. An identical-sequence candidate gets no borrowed value; choosing the other candidate's Evidence ID rejects. This passes in test_explicit_null_never_falls_back_to_equal_sequence_or_other_lot.
3. **Nested JSON and recorded unit identity.** Reordered object keys remain equivalent, but array order, nested false versus zero, and nM versus NM stay separate without rewriting input. Four variants pass in test_nested_context_keeps_original_types_array_order_and_unit_case.
4. **Late fallback across a project switch.** The independent browser test forces one failed observation request, holds its old-project fallback, checks updating/no scalar/disabled ordering controls, switches projects and selects a new cohort, then releases the old fallback. New-project values, options, context and ID-only persistence remain unchanged. No outbound request or JavaScript error occurs.

An initial independent browser harness run raced its own redundant same-project initialization, so its disabled-control assertion ran against the previous ready DOM. The harness now waits for actual project readiness before injecting the failure. It then passed both its focused execution and the final full replay. No product code was changed for that harness issue.

## Source findings and mandatory gates

Identity and provenance: PASS in the tested scope. Measured observations resolve through Material → Construct → Molecule; equal sequences do not confer identity. Evidence kind, exact metric/unit, type-aware conditions, assay and actual source/version define an ordering policy. Multiple observations require an explicit Evidence-ID choice, including equal values or null. Cohort membership can be restored from any eligible original member ID. Unknown or incompatible context remains inspectable and unranked. Stored source data are unchanged, and saved snapshots equal their original records.

Security: PASS for retained local controls and observed browser traffic. Project classification is an explicit existing provenance field with research as the initial default; the project title does not infer synthetic status. Synthetic supplementary maps require the explicit fixture class and exact known fixture sequences. Browser persistence stores observation IDs/direction rather than values, conditions or sequence payloads. This is not a complete endpoint/OS audit or ASVS certification.

Regression: PASS. The final full Python and all retained browser suites passed. A previously reported structure-save detached-DOM failure was reviewed: the old browser helper could accept a pre-save viewer while asynchronous reload was still pending. The current product disposes the viewer and makes content inert during reload; the test waits for the actual saved source/map revision before proceeding and retains physical canvas assertions. The final eleven-check structural replay passes.

Async observation race: PASS. refreshObservations checks both monotonically increasing request identity and current project identity after the initial and fallback responses. Loading rows expose no old scalar and ordering controls are disabled. The added independent delayed-fallback browser replay verifies the old response cannot overwrite the new project context.

Acceptance bookkeeping: PASS for the tested fail-closed checks. Named main/two-negative results, reviewer, report/source hashes, source inventory and exact current source digests are required before a journey can be registered PASS. Source/report changes, missing/failed/duplicate named negatives, wrong reviewer, absent commit and path escape reject. The implementation commit must still be recorded by the integration agent; this report authorizes only the exact source digest above. Documentation registration may update the counts to J01 1/8 and prescribed negatives 2/16; it cannot grant other journey acceptance.

No unresolved P0/P1 issue was identified within the reviewed F09/J01/M2 engineering scope. This is not a claim about unimplemented journeys.

## Passage boundary and remaining evidence

F09 and the full synthetic-fixture J01 engineering path may integrate with this exact tested source. The original M2 engineering gate is met by full J01 plus the retained J03 structural-observation foundations, selection preservation and numbering/structure negative cases. Earlier F07/F08 reports correctly left M2 pending while this J01 observation path was missing; this review supplies that missing engineering evidence.

Seven full journeys remain unaccepted. J03's saved hypothesis/design steps and later M3/M4 functionality are not passed by a structure-viewer replay. The eighteen human-validated scientific golden examples, biological accuracy, eight-role researcher evaluation, final branch coverage, standard-hardware latency/storage/security measurements, all eight restart paths and final 8/8 + 16/16 integration remain pending. Synthetic tests do not become measured experiments or human scientific validation, and M2 engineering PASS does not imply Release 1.0 completion.

## Independent mission-alignment assessment

Mission-alignment verdict: **PASS** for this milestone and the requester-authorized checkpoint documentation.

The addition to AGENTS.md makes the original charter, eight researcher questions and ACs an explicit recurring checkpoint at meaningful milestones, context compaction and priority changes. It requires correcting scope drift, disproportionate engineering effort and incidental polish, treating follow-up examples/corrections as constraints unless explicitly promoted, and independently assessing mission alignment. The original hierarchy, safety and independent-verification rules remain intact. The English/Japanese PRODUCT_ALIGNMENT documents agree on the researcher's responsibility for scientific judgment and explicitly preserve personas, journeys, scientific definitions, data sharing and completion conditions.

F09 serves P01's original question through one coherent saved research action: inspect candidates, compare original evidence, select a shortlist and preserve why. Exact-context ordering is necessary J01 behavior, and conservative explicit choices avoid inventing comparability. The useful evidence is the persisted shortlist and its original subjects/sources, rather than the number of tests or controls. Engineering fixtures establish operation; they do not establish actual researcher usefulness or biological validity.

The largest product gap is the disconnected design/reasoning path: users cannot yet make a named-residue child variant, inspect preserved parent/child differences, and retain a supported research hypothesis. The documented next priority—M3's connected parent/reference → numbered substitution → child differences → hypothesis/evidence path, then molecular composition and M4 comparisons/decisions—is consistent with the plan. Reuse the current identity, numbering and evidence contracts, keep measured parent data on their original subjects, and develop one AC-linked research action at a time. Additional standalone controls, prediction engines, terminology/cosmetic work or technical sophistication would not close the seven remaining journeys and should require a demonstrated research-flow need.

The original full runtime replay manifest is preserved as M2-observation-independent-runtime-replay-source-manifest.json with source digest `1ac9421ff8b7c4d852e3b9e5cbc60332a86053face3a3dea4d5361f3fc82652d`. Following that replay, only the authorized AGENTS.md checkpoint changed within the inventoried source set. Comparing both complete file inventories and every digest confirmed AGENTS.md was the sole difference; all runtime, test, script and other inventoried file digests match the replay snapshot exactly. The final independent source manifest includes this inspected documentation change. The new bilingual alignment documents are reviewed as documentation and explicitly label the 800-candidate evidence as synthetic engineering verification. Browser assertions are not rerun for that documentation-only delta, and no new runtime behavior is claimed from it.

Documentation SHA-256 reviewed after the freeze:

- AGENTS.md: `7796171452078e3926b175091079b595d14799ec378a0e6488e4639e832fcf17`
- docs/PRODUCT_ALIGNMENT.md: `4bfa612fa3814adaf0e73bd5e1781a7fd682f165baf757412e872d5cd92ac0a5`
- docs/PRODUCT_ALIGNMENT.ja.md: `28a8ca07757c93415b48648dddcd9671d5b343a27af8e298038e839016d34764`
