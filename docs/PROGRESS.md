# Development progress

Target: all eight researcher workflows and sixteen prescribed browser edge cases, with no open P0/P1 defects.
The complete release goal remains active.

| Stage | Status | Evidence or remaining gate |
|---|---|---|
| M0 specification/design | PASS | Independent review, eight scenario definitions, source boundaries and rendered four-screen prototype |
| M1 initial F01–F05 | PASS for initial slice only | 55 tests and 10 Chrome checks independently replayed; see TEST_EVIDENCE/M1-initial-independent-review.md |
| M1 complete foundation | Engineering gate PASS | 104 tests and 11 Chrome checks independently replayed; F06 adds BindingUnits, ordered component graphs, copy counts, origins and composition Lineage; human scientific golden fixtures remain pending |
| M2 exploration/observation | F07 PASS; full M2 remains PARTIAL | Independent replay: 159 Python tests and 5 F07 Chrome checks. Imported source-bearing IMGT maps, separate raw/numbered chain/domain identity and complete CDR-H3 grouping. Structure correspondence/viewer and assay-aware sorting remain pending |
| M3 design/evidence | Not started | Variants, graph composition, lineage, hypotheses and J02/J04/J05 |
| M4 experiments/decisions | Not started | Measurement CSV, construct comparison, criteria, weights, finalized decision revisions and J06/J07 |
| M5 quality integration | Not started | Full J08 formats, 8/8 + 16/16, branch coverage, security/performance, independent full replay |

Full workflow acceptance: **0/8**.
Prescribed final browser edge cases: **0/16**.
Partial domain and browser checks are tracked separately; no percentage is inferred from the number of tests.
The initial code has no validated predictive model and no asserted biological prediction accuracy.

Next implementation dependencies: F08 structure parsing/viewing with explicit model/chain/residue correspondence, preserved camera and separate model-internal confidence; then assay-aware observation sorting. Public PDB/mmCIF, IMGT, viewer and parser sources have been researched; no new runtime dependency or structure code is integrated yet.
Human-validated scientific fixtures and actual researcher evaluation remain explicit open requirements.
