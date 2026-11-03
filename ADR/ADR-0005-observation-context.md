# ADR-0005 Numeric ordering with explicit evidence context

- Status: design PASS; implementation review pending before integration.
- Date: 2026-11-03, Asia/Tokyo. Owner: implementation agent.
- Related: P01/P04/P06/P07, J01/J04/J06/J07, AC-J01/AC-J04/AC-J06/AC-J07; F09, required M2 observation and J01 completion.
- User action: choose an actual metric/assay/source context in E, inspect original units/conditions, explicitly choose an observation when a candidate has multiple eligible material results, order candidates ascending/descending, compare two candidates in W, retain five IDs and the reason/evidence in R across restart.
- Input/output: existing Evidence/Material/Construct/Molecule records → transparent numeric ordering, missing/ambiguous/different-context statuses, immutable shortlist draft. Existing data is never changed or aggregated.
- Option A: compare only matching recorded kind, metric, unit, nonempty conditions with explicit assay, actual source name/version; retain each sample/evidence identity and require choice for multiple observations.
- Option B: collapse all values with the same metric into an average or silently use latest/first. Reject B because it conflates units, conditions, samples and measured/computed evidence.
- Proposed choice: A. Matching metadata is necessary for this ordering policy, not proof of scientific comparability or an automated candidate-selection recommendation. Source-version/assay/conditions unknown stays explicit and unranked. Raw evidence remains inspectable in R.
- Missing values: null remains missing and sorts after actual numbers in either direction; zero remains a number. No score, mean, imputation, unit conversion, scientific threshold or success prediction is generated.
- Identity/provenance: numeric choices use immutable Evidence IDs, with direct Material/Construct/Molecule path. Computed results remain separate from measured data and never become the latter.
- Confidentiality: local API/UI only. Persist only cohort representative Evidence ID, explicit per-candidate Evidence IDs and ordering direction; never numeric values, condition payloads or sequences in localStorage.
- Compatibility: no persisted schema change or data migration. Existing fields are read without normalization. Old imports remain valid; incomplete context only disables numeric ordering, not raw viewing.
- Priority: required missing J01/M2 behavior; mandatory identity/provenance/security/regression gates apply. No discretionary functionality is added.
- Tests: complete e2e_j01_candidate_shortlist with800 candidate sequences/QC, imported CDR-H3 grouping, explicit binding-context sorting, W two-candidate observation, E five selections, R reason/evidence preview/save, actual process restart and exact IDs/reason/source snapshots. Two prescribed negatives: e2e_j01_invalid_sequence and e2e_j01_missing_measurement.
- Additional negatives: incompatible units/conditions cannot enter one ordering; ambiguous repeated samples require an explicit evidence choice; malformed/stale choices reject without persistence; independent reviewer adds two boundaries.
- Non-goals: assay validation, conversion, statistical aggregation, final weighted decision, construct-design editing, variants or full J04/J06/J07. M3/M4 remain required.
- Reviewer: `/root/independent_review`, TEST_EVIDENCE/M2-observation-design-review.md, 2026-11-03. Rollback: isolate fixture DBs; no persisted fields or existing entities are rewritten. Escalate if review identifies changed scientific semantics or product scope.
