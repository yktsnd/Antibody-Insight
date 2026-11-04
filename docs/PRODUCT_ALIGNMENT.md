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

## Current assessment: F16–F18 / J06

P06's complete synthetic engineering action now works through independent replay: select an actual antibody Molecule, register and compare two distinct Constructs, follow three actual Materials/lots, explicitly map measurement CSV source tokens, inspect each original expression/quality observation and retain a proposed explanation, limitations and next controlled experiment. Original subject IDs, units, typed conditions, assay source/version and separate file/importer provenance survive actual restart and fresh export/reimport. Raw CDS positions do not imply translation correctness or expression causality. Missing observations remain unknown; matching metadata does not establish biological comparability or independent replicates.

Current independent engineering acceptance is J01–J06, six main journeys and twelve prescribed negatives, at actual source commit `2c2a96ffe67dc58ab8110b72c839a3948288a914`. Final review is `TEST_EVIDENCE/M4-experiments-final-independent-review.md`. M4 remains unfinished because J07 is absent; full J08, human scientific goldens, actual researcher evaluation and final release gates remain open. The separate public experimental 1MLC observation check remains a source/scale test, not biological validation.

Benchling's actual-entity links, Skyline's source/condition grid and explicit two-input sequence comparison patterns informed native forms and tables. Existing IDs, strict atomic persistence, exact F09 contexts, W source paths and R proposed hypotheses were reused. A new alignment, translation, statistical or prediction engine would not serve this action better. Independent review caught old file-read errors affecting newer approved reviews; ownership guards and localized readout updates preserve current drafts. Lossless approved JSON transfer corrects numerical representation changes without inventing values or rewriting old research data.

The largest remaining barrier is J07: inspect actual criteria/weights, missingness and trade-offs, retain original evidence, then finalize and revise an immutable research decision. Complete it before adding unrelated design controls or predictors. Verified JMP and Galaxy documentation informs the proposed R extension; ADR-0010 remains a design proposal pending independent review. Then complete J08's adapters/reproducibility and final integration. Test counts and technical sophistication cannot substitute for scientific utility or evaluation by researchers.
