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
| M5 quality integration | Not started | Full J08 formats, 8/8 + 16/16, branch coverage, security/performance, independent full replay |

Current independent workflow engineering acceptance: **7/8** (J01–J07, labelled synthetic fixtures; commit `b7eabac`).
Prescribed browser edge cases: **14/16** (J01–J07).
Partial domain and browser checks are tracked separately; no percentage is inferred from the number of tests.
The initial code has no validated predictive model and no asserted biological prediction accuracy.

Next: complete J08's supported prediction-JSON adapters and full input/export/fresh-store reproducibility path, then all final release gates. Reuse actual IDs, existing source contexts, immutable snapshots and hypotheses. Benchmark relevant established scientific tools before each major interface. Do not count shared plumbing as another complete journey or add isolated design controls ahead of missing research actions.
Human-validated scientific fixtures and actual researcher evaluation remain explicit open requirements.
