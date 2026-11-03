# Product alignment checkpoint

[日本語](PRODUCT_ALIGNMENT.ja.md) · [Original charter](../PRODUCT_GOAL.md) · [Execution specification](../DEVELOPMENT_PLAN.md) · [Progress](PROGRESS.md)

The researcher must be able to observe an antibody, investigate a question, compare evidence, design an experiment or variant, and retain the reasoning for the next person. Scientific correctness, freedom to inspect and transparent judgment take priority over feature count. The software supports the researcher's judgment.

At each meaningful milestone, after context compaction and when priorities change:

1. Re-read the charter, the affected persona's actual research question, its complete E/W/D/R journey and AC. A follow-up example or terminology correction constrains that work; it does not automatically become another product feature.
2. Describe what the researcher can now observe, understand or decide, using an actual saved result. Check the direct molecule/construct/material/residue identity, original evidence, conditions and uncertainty.
3. Identify the largest remaining obstacle to a coherent research action. Prefer completing that action over adding another isolated capability. Look for simpler ways to achieve the same scientific result.
4. Review effort versus user value. Benchmark at least two relevant established scientific tools before each major interface and record UX references and a reuse-versus-build justification in [SCIENTIFIC_UX.md](SCIENTIFIC_UX.md). Prefer familiar scientific navigation, dense useful data, exact units/identities, direct manipulation and synchronized views with progressive disclosure. Correct scope drift, overengineering, decorative dashboards, repeated incidental polish and attention to engineering metrics that does not improve research use. Keep necessary scientific, provenance, confidentiality and regression gates.
5. Have an independent reviewer assess both usefulness and implementation. Preserve unfinished work explicitly. A test pass or engineering fixture cannot stand in for scientific validation or actual researcher evaluation.

This checkpoint supplements the original specification. It changes no persona, journey, scientific definition, sharing policy or completion condition.

## Current assessment: F14/F15 / J05

P05's continuous research action now works in the independently verified synthetic engineering path: select actual source BindingUnits, explicitly declare chain/part/linker order and copies, review actual source usage before saving, inspect saved sequences/source IDs, compare another design and retain the unverified question and next experiment. Source intervals, component IDs, declared connections and exact composition Lineage survive restart/export/reimport. Reusing an equal sequence never collapses source identities. Missing paired-source chains and partial/unequal usage stay visible; declared source-chain occurrences do not establish complete functional units, valency or physical assembly.

Current independent engineering acceptance is five complete journeys (J01–J05) and their ten prescribed negatives on the recorded source. M3 meets its engineering gate. J06–J08, scientific golden validation, actual researcher evaluation and final release quality gates remain open. Neither test counts nor synthetic fixtures establish biological validity or practical acceptance. The separate public experimental 1MLC source/scale check remains an observation test, not a predictor or scientific-golden validation.

The established Benchling/HELM component/source patterns, existing declared graph, local atomic persistence, W inspection and R hypotheses were reused. Native ordering and task controls avoid displaying unrelated design forms together. Independent review found and corrected automatic reuse of a deleted component ID reconnecting an unrelated part, and stale save errors altering a newer confirmation. Source identity and draft ownership, rather than more design features, determined the fixes.

The largest remaining barrier is connecting actual expression constructs/materials to meaningful experimental comparisons (J06). Complete M4's construct differences, explicit measurement source/sample mapping, original units/conditions and next controlled experiment. Then finish J07's researcher-defined criteria/weights, missing-data controls and immutable finalized decision revisions, followed by J08's complete adapters/reproducibility and final integration gates. Reuse current IDs, exact contexts and snapshots; benchmark at least two relevant established scientific tools before each major interface. Avoid unrelated prediction engines, additional isolated composition controls and cosmetic expansion ahead of these missing research actions.
