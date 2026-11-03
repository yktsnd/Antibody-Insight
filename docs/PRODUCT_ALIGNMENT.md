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

## Current assessment: F12/F13 / J03/J04

The useful outcome is a continuous source-to-question action. P03 compares explicitly scoped complex sources, observes an exact mapped or source-only residue, checks model-internal metrics and saves a proposed variant hypothesis with limits and a next experiment. P04 follows property evidence to a source-reported position, inspects the actual sequence/structure and measured versus computed source, creates a distinct child and retains the next controlled test. A source position association does not establish causality or localize a whole-Material measurement. Parent measurements and all original source records remain unchanged.

Current independent engineering acceptance is four complete journeys (J01–J04) and their eight prescribed negatives on the recorded current source. The other four complete journeys remain open. Scientific golden validation, actual researcher evaluation and final release quality gates remain open too. Test counts and synthetic source fixtures do not establish biological validity or practical acceptance. Public experimental 1MLC separately verifies real antibody-scale source preservation/rendering, without predictor-confidence or scientific-golden claims.

The native local viewer's existing styles/focus operations, exact identity model, source numbering, numeric contexts and immutable save mechanism were reused. No new renderer, analysis engine, secondary-structure inference or arbitrary score was introduced. Independent review corrected an asynchronous hypothesis-opening context defect and verified byte preservation of the public coordinate fixture.

The largest remaining coherent-action gap is J05 interactive molecular composition. Next implement explicit chains/ordered parts/linkers and source BindingUnit identities with design comparison and a retained unverified question, using the existing component graph. Then finish J06 construct/material comparison, J07 finalized criteria/revisions and J08's complete adapters/reproducibility path. Benchmark at least two relevant established scientific tools before those interfaces. Avoid unrelated prediction engines, broad UI replacement and incidental expansion ahead of these missing research actions.
