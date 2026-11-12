# F29 independent journey integration review

**PASS** · 2026-11-12T08:49:24.608966+00:00 · Reviewer `/root/observation_review`

The independent Chromium replay verified 8/8 main journeys and 16/16 prescribed negative cases against the names in `TRACEABILITY.csv`.
The frozen snapshot contains 112 source files with aggregate SHA-256 `553e42a4221902fa45852ba11163130e6bfc8ab1ca47728f1fc93473111ebfbb`. The byte-copied working-tree snapshot was rehashed after testing.
Each harness created its own temporary SQLite database. Cases used labeled synthetic fixtures. The J03/J04 harness also ran its separate public experimental structure source and scale check.

| Journey | Harness | Exact result names | Result file |
| --- | --- | --- | --- |
| J01 · PASS | `node tests/j01-browser.cjs` | `e2e_j01_candidate_shortlist` (PASS)<br>`e2e_j01_invalid_sequence` (PASS)<br>`e2e_j01_missing_measurement` (PASS) | `TEST_EVIDENCE/J01-browser-results.json` |
| J02 · PASS | `node tests/j02-browser.cjs` | `e2e_j02_humanize_variant` (PASS)<br>`e2e_j02_numbering_unavailable` (PASS)<br>`e2e_j02_insertion_mapping` (PASS) | `TEST_EVIDENCE/J02-browser-results.json` |
| J03 · PASS | `node tests/observation-journeys-browser.cjs` | `e2e_j03_complex_comparison` (PASS)<br>`e2e_j03_unmappable_residue` (PASS)<br>`e2e_j03_missing_confidence` (PASS) | `TEST_EVIDENCE/J03-browser-results.json` |
| J04 · PASS | `node tests/observation-journeys-browser.cjs` | `e2e_j04_developability_review` (PASS)<br>`e2e_j04_unit_mismatch` (PASS)<br>`e2e_j04_unknown_assay_condition` (PASS) | `TEST_EVIDENCE/J04-browser-results.json` |
| J05 · PASS | `node tests/j05-browser.cjs` | `e2e_j05_bispecific_composition` (PASS)<br>`e2e_j05_undefined_chain` (PASS)<br>`e2e_j05_unsupported_analysis` (PASS) | `TEST_EVIDENCE/J05-browser-results.json` |
| J06 · PASS | `node tests/j06-browser.cjs` | `e2e_j06_construct_sample_lineage` (PASS)<br>`e2e_j06_unknown_sample_id` (PASS)<br>`e2e_j06_incomparable_units` (PASS) | `TEST_EVIDENCE/M4-J06-browser-results.json` |
| J07 · PASS | `node tests/j07-browser.cjs` | `e2e_j07_candidate_decision` (PASS)<br>`e2e_j07_missing_required_metric` (PASS)<br>`e2e_j07_immutable_decision` (PASS) | `TEST_EVIDENCE/M4-J07-browser-results.json` |
| J08 · PASS | `node tests/j08-browser.cjs` | `e2e_j08_export_reimport` (PASS)<br>`e2e_j08_duplicate_id` (PASS)<br>`e2e_j08_corrupted_structure` (PASS) | `TEST_EVIDENCE/M5-J08-browser-results.json` |

F29 lets a researcher compare original values in R and inspect the original subject and source before retaining a shortlist or decision. It reuses the exact recorded-context rule and the existing Evidence cards.
Independent F29 edge replay verified typed conditions, signed-zero values, repeated events, the candidate scope and exact provenance, retained decision fields, and an unchanged stored bundle.
A provenance-backed end-to-end material case and actual researcher evaluation remain pending. These results establish engineering acceptance for the named fixtures.

The source manifest, result-file SHA-256 digests and named case audit accompany this report.
