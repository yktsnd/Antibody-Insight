# F14/F15 composition design: independent review

Design verdict: **PASS under the recorded scientific constraints.** Implementation, complete J05, M3 and Release 1.0 remain **NEEDS-EVIDENCE**.

Reviewer: `/root/observation_review`. Date: 2026-11-03, Asia/Tokyo. Reviewed PRODUCT_GOAL, DEVELOPMENT_PLAN J05/AC-J05 and data model, AGENTS, current alignment/traceability, ADR-0008 after its clarifications, COMPONENT_CONTRACT, existing graph validation and W display, L03/L11, and SCIENTIFIC_UX's J05 benchmark. No product source was implemented or edited; no broad tests were rerun. Current acceptance remains **4/8 journeys and 8/16 negatives**.

## Research action and reuse

Trace: F14/F15, P05, J05, AC-J05. The missing action is E selecting two actual BindingUnits → D explicit chains/ordered parts/linkers/copies → reviewed new Molecule → W whole/each-chain inspection → D another saved composition and comparison → R proposed question → restart/export/reimport. It lets the researcher inspect what each chain contains, its actual origin and what another design changes. Existing graph serialization alone does not satisfy that action.

I independently checked [Benchling Biologics component/chain/format documentation](https://help.benchling.com/hc/en-us/articles/45868988869261-Configure-Benchling-Biologics-schemas-and-formats) and [Pistoia HELM tools](https://pistoiaalliance.atlassian.net/wiki/spaces/HELM/pages/2673279069), with the [upstream antibody editor](https://github.com/PistoiaHELM/HELMAntibodyEditor). The relevant patterns are part→chain→whole hierarchy and explicit connections. Benchling's licensed service/glyphs and HELM's automatic domain/chemical operations are not adopted. HELM's separate graph/chemistry dependency notices also need review before any future integration. This is primary-document comparison, not actual researcher evaluation.

Reuse of existing interval origins, component graphs, immutable preview/save, W inspection and R hypotheses is appropriate. A narrow native ordered-part table solves the missing local interaction more simply than requiring hand-authored JSON or installing/building a chemical graph editor. No new renderer, analysis engine, monomer library, automatic pairing or arbitrary design score is justified here.

## Scientific constraints accepted into ADR-0008

- Source parts resolve exact same-project BindingUnit/chain/inclusive raw intervals on the server; independently entered parts/linkers require actual sequence and role. No default source, partner, linker, copy count or format interpretation. Equal sequence does not merge source identities.
- Coverage stays per actual source chain/interval/component instance, with declared copies separate. Missing paired chains, partial use and copy imbalance stay visible. Selected IDs or union coverage do not establish complete functional units, valency or pairing. Deliberately partial declarations are not automatically completed or labelled functional.
- Preserve component IDs/endpoints through reorder and parent copying. Deleted/renamed references cannot retarget a neighbouring row or equal sequence; dangling references must reject save until explicitly repaired.
- Only provenance/Lineage graphs require acyclicity. Declared connection cycles remain possible under existing endpoint validation, without chemical-validity inference. Connections describe component definitions, not individual contacts among repeated copies; L11 remains open.
- Initial designs have no invented parent. Explicit derivatives require a real parent, reason and exact before/after signatures; do not manufacture a change solely to authorize Lineage. New molecules inherit no measurements, Constructs/Materials, verified numbering or structure. Optional local-entry design notes are annotation Evidence with null numeric value; subsequent hypotheses remain proposed.
- No validated whole-molecule adapter is installed. Expose actual analysis unavailability/scope rather than a successful result, fake format-compatibility judgment or dummy analysis action. Existing source maps/structures remain inspectable only on their actual identities.

These constraints preserve existing scientific meaning and the original J05; they do not approve chemistry, automated domain recognition, external sharing or a new identity model.

## Independent implementation edges and gates

1. **Equal origins/partial paired use:** distinct equal-sequence units, overlapping/repeated intervals, missing partner and imbalanced copies must retain exact source/instance identities without inferred completeness. Wrong project/unit/chain/interval rejects atomically.
2. **Ordering/connections/cycles:** reorder and copy a connected recipe, then delete/rename a referenced part. Keep endpoint identity, reject dangling references, and distinguish allowed declared connection cycles from forbidden provenance/Lineage cycles.
3. **Undefined composition:** empty/duplicate chains, omitted/bool/noninteger/zero copies, empty parts or missing linker sequence cannot become an arbitrary chain, one copy or conventional linker. Every saved chain must match its complete ordered sequence graph.
4. **Comparison/async ownership:** missing/renamed chains, equal sequences with different origins and absent graphs must remain explicit rather than imply homology. Held preview/save responses cannot overwrite another project or newer recipe. Molecular and source-unit selections remain separate; recipes, sequences and scientific drafts never enter localStorage.

The main browser test must perform the full original action using paired and single-chain sources, real controls/reordering, a second composition with actual Lineage, source inspection, retained question, real process restart and exact fresh reimport. Keep prescribed negatives `e2e_j05_undefined_chain` and `e2e_j05_unsupported_analysis`; the latter must verify real unavailable scope and absence of engine/results, not a dummy endpoint. Preserve all J01–J04 regressions and historical evidence; archive new evidence bytes before registration.

Identity/provenance/confidentiality/reuse design gates: **PASS**. F14/F15 may proceed to implementation. Independent implementation/full-J05 replay, scientific goldens, researcher evaluation and final release gates remain required. No unresolved product-purpose choice in this bounded design requires user escalation; this is not approval to expand the scientific scope or count J05 as accepted.
