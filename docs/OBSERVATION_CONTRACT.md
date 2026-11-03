# F09 evidence ordering contract

This is an observation policy, not a scientific claim that matching metadata proves measurements comparable.
It implements the missing numeric-ordering step in J01 and supplies consistent boundaries for J04/J06/J07.

## Cohorts

Eligible records have kind measured or computed; a nonempty metric/unit; an actual nonempty source name and known version; and nonempty conditions containing a nonempty string `assay`.
Null/empty conditions, missing assay identity or unknown version remain explicit and cannot establish a numeric-ordering cohort. No source data is modified or replaced with a placeholder.
The cohort key compares kind, metric, unit, exact JSON/type-aware conditions and source name/version. Units are case-sensitive recorded symbols; no conversion, lowercase alias or normalization is inferred. Source files/runs with different recorded versions remain separate.
An opaque cohort ID is a representative Evidence ID. Its label displays all original context, but values/conditions are not put in localStorage.

Each eligible evidence record resolves to a molecule using its actual subject path. Measured records retain their Material→Construct→Molecule path. Computed structure records use their declared Structure→Molecule path. Kinds never mix.
No candidate score is derived from another molecule's matching sequence or lineage.

## Explicit choices and ordering

The API receives project ID, selected cohort ID (or no cohort), per-molecule Evidence-ID choices, and direction ascending/descending.
Malformed objects, unknown molecule IDs, blank choice IDs, stale IDs, wrong subjects and observations outside the chosen cohort reject clearly.
A candidate with exactly one matching observation may display it. Multiple matching observations require explicit choice, even if all values are numerically equal. There is no first/latest/mean fallback.
With no choice, ambiguous, missing or different-context candidates retain explicit statuses and do not acquire a scalar value. Actual null values are labeled missing, while0 remains0. Numeric values order normally, followed by all unavailable/ambiguous statuses in both directions. Stable ID/external-label ordering breaks ties; it is not a biological preference.
Selecting a cohort never changes the candidate selection set. CDR grouping remains a separate view control. E/W/D/R navigation, source inspection, shortlist evidence snapshots and restart preserve the chosen IDs/context.
R continues to show original evidence of other units/conditions separately. This policy does not hide raw data or automatically average it.

## J01 executable evidence

The fixed synthetic engineering dataset contains800 accepted single-chain candidates, two distinct candidates for observation, exact CDR-H3 groups, distinct valid duplicate sequences, measured binding context, a true zero, a missing value, unknown-condition and alternate-unit records, and multiple-material ambiguity.
Separate invalid input rows are shown/excluded only after explicit preview, with800 accepted records retained.
The browser must actually choose context and ambiguous observations, inspect two candidates, select five IDs, save reason+sources and restart the process. It then compares saved IDs/reason/evidence snapshots exactly.
Fixture results do not satisfy the human-validated scientific golden-data or real-user evaluation requirements.
