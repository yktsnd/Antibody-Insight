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

## Current assessment: F09 / J01

The useful outcome, verified with clearly labelled synthetic engineering fixtures, is a source-bearing shortlist: 800 accepted candidates can be inspected by imported CDR-H3 groups and a chosen binding context, two candidates compared, and five IDs with their reason and original evidence retained after restart. Exact-context ordering is conservative and requires explicit sample choices; it does not prove assay comparability or make a biological recommendation.

The product is still incomplete. Variants, research hypotheses, interactive molecular composition, construct/measurement comparison and finalized decision revisions are the main missing links. The other seven complete journeys remain open; human scientific golden validation, real researcher evaluation and the final quality gates remain open too.

The next priority is M3's connected parent/reference → numbered substitution → child differences → hypothesis/evidence path, followed by composition and M4's experimental comparisons and decisions. Reuse the existing identity, evidence and numbering contracts. Avoid new prediction engines, automatic scientific interpretation, cloud services, cosmetic expansion and further terminology work unless they remove a demonstrated obstacle in those journeys.
