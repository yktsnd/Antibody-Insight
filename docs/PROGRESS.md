# Development progress

Target: a scientifically rigorous, useful workspace in which all eight researcher personas can observe, compare, design and retain evidence-based reasoning across their complete workflows.
The eight journeys, sixteen prescribed browser edge cases and zero open P0/P1 defects are acceptance evidence for that product, alongside scientific validation and actual researcher evaluation.
The complete release goal remains active. Revisit the [product alignment checkpoint](PRODUCT_ALIGNMENT.md) ([日本語](PRODUCT_ALIGNMENT.ja.md)) at milestones, after compaction and when priorities change.

| Stage | Status | Evidence or remaining gate |
|---|---|---|
| M0 specification/design | PASS | Independent review, eight scenario definitions, source boundaries and rendered four-screen prototype |
| M1 initial F01–F05 | PASS for initial slice only | 55 tests and 10 Chrome checks independently replayed; see TEST_EVIDENCE/M1-initial-independent-review.md |
| M1 complete foundation | Engineering gate PASS | 104 tests and 11 Chrome checks independently replayed; F06 adds BindingUnits, ordered component graphs, copy counts, origins and composition Lineage; human scientific golden fixtures remain pending |
| M2 exploration/observation | Engineering gate PASS | Independent F09 replay: 252 Python tests; retained11/numbering5/structure11/J01five/independent-race3 Chrome checks, all exit0. Full synthetic J01 and original J03 observation foundation are verified; full J03 hypothesis/design remains M3. See TEST_EVIDENCE/M2-observation-independent-review.md |
| M3 design/evidence | Engineering gate PASS | F10–F15 and full synthetic J01–J05 independently verified on frozen source:352 Python tests and67 browser checks, all exit0. Explicit source-part composition, source-usage review, design comparison, exact Lineage and proposed questions work through restart/export/reimport. Scientific/user/release gates remain open |
| M4 experiments/decisions | Engineering gate PASS | F16–F20 and full synthetic J06/J07 with retained J01–J07 independently verified on frozen91-file source:452 Python tests,37 retained browser checks and12 additional independent browser suites all PASS. Required missingness, original observations, proposed hypotheses, fixed decisions/revisions and typed restart/fresh transfer are verified; scientific/user/release gates remain open |
| M5 quality integration | Engineering workflows PASS; overall quality exit incomplete | F21/F22 design/domain/API/UI and frozen all-eight integration independently PASS on103-file source:538 Python tests,22 Node suites plus actual1000-value native-source browser checks; core branches548/566=96.82%. All8 main flows+16 prescribed negatives registered. Standard-hardware performance and human scientific/researcher evaluation remain pending; host p95≈327ms exceeds300ms |

Current independent workflow engineering acceptance: **8/8** (J01–J08, labelled synthetic fixtures; source commit `a82cc0f3861bd24e89b2634ee2fe32826043be97`; [independent review](../TEST_EVIDENCE/M5-final-independent-review.md)).
Prescribed browser edge cases: **16/16** (J01–J08).
Partial domain and browser checks are tracked separately; no percentage is inferred from the number of tests.
The initial code has no validated predictive model and no asserted biological prediction accuracy.

Next: obtain the eighteen human-verified scientific inputs/expectations and actual eight-role research evaluations, and repeat the ten-run latency test on verified8logicalCPU/16GB/SSD hardware. [Gate registry](../TEST_EVIDENCE/M5-release-gates.json) preserves the nonstandard host's observed above-threshold p95. Use the [human evaluation packet](../validation/README.md). Correct issues demonstrated by real research tasks; do not replace this work with unrelated prediction/design features, incidental polish or test-count goals.
Human-validated scientific fixtures and actual researcher evaluation remain explicit open requirements.
