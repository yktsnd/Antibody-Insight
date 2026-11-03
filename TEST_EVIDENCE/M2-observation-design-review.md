# F09 contextual numeric ordering and J01: independent design review

Design verdict: **PASS**, with the fixture/identity clarifications below.
Implementation and complete J01 execution: **NEEDS-EVIDENCE** until independently replayed.

Reviewer: `/root/independent_review`, separate from implementation.
Date: 2026-11-03, Asia/Tokyo.
Baseline: `23e8022f07a0b4d03c3b5b96493386ec8888a15c` plus proposed ADR-0005 and OBSERVATION_CONTRACT.
Authority: PRODUCT_GOAL and original DEVELOPMENT_PLAN J01/AC-J01. Related shared boundaries: P04/P06/P07, J04/J06/J07 and their ACs; those complete journeys are not authorized as passed by this design.

## Scope and required action

P01/J01/AC-J01: E imports/QCs 800 candidate sequences, explicitly groups by imported heavy-chain CDR3 and orders recorded binding values within a selected context; W observes differences between two candidates; E retains five selected IDs; R previews/saves reason and original evidence; a real restart restores the exact five IDs, reason and evidence snapshots.

The input is existing immutable Molecule/Construct/Material/Evidence and imported numbering data. Output is a transparent ordering/view and immutable shortlist draft, not an averaged score, biological ranking recommendation, final weighted decision or prediction. No entities or source metadata are normalized or rewritten. This is mandatory missing J01 observation behavior, not discretionary feature expansion.

## Identity, provenance and scientific boundary

Exact kind/metric/unit/source name/version/type-aware conditions with an explicit assay is a conservative **ordering policy**. It does not establish experimental comparability. Unknown version/assay/conditions cannot be filled in from another record, a metric label or a project title. Units remain case-sensitive; no conversion or synonym is inferred. Raw records of other contexts remain accessible in R.

Measured records retain Material → Construct → Molecule; computed structural records retain Structure → declared Molecule. Same sequence, parentage, construct label or antigen reference cannot replace the named direct subject. Measured and computed records never form one cohort.

Several observations in the same cohort require a named Evidence-ID choice even when their values are equal, belong to one Material, or include one null. Do not select the latest, first or only nonnull value implicitly. A missing value remains missing, zero remains numeric and finite negative values remain supplied numbers; unavailable/ambiguous/different-context results follow numeric values in both directions without a fabricated scalar.

The selected cohort is defined by an existing immutable Evidence ID. It must remain resolvable when input order changes or more cohort members are appended, even if the displayed representative changes. Accepting any eligible cohort member as the defining ID is a safe way to preserve that context without persisting conditions. Reject stale/unknown/wrong-subject choices, malformed choices and choices supplied without a selected cohort. An explicit cohort change may clear incompatible observation choices but must retain candidate selections.

Persist IDs and direction only. Do not put numeric values, conditions payloads or sequences in localStorage. The R preview and saved snapshots must include the actual selected observations used in the J01 reason, with original subjects/conditions/source/time; the full M4 weighted/criteria decision is still separate future work.

## Faithful J01 fixture and replay

The original J01 requires **two candidate observations**, not two chains within each candidate. Eight hundred single, explicitly declared heavy-chain candidate records are adequate. Remove the extra mandatory “two-chain examples” wording from the fixture contract; retaining such examples as optional extra coverage does not change J01's gate. No VH/VL pairing, IgG format or biological antibody validity is inferred.

1. Build a documented synthetic **sequence CSV** with exactly 800 valid accepted records plus separately identified missing-sequence and invalid-symbol rows. Include distinct external IDs sharing a valid duplicate sequence and several similar/CDR3 groups. The preview must show excluded rows and repeats without saving. The browser explicitly confirms saving the 800 valid candidates.
2. Expose Project.data_class when creating the project, with **research as the default** and an explicit synthetic_fixture choice for these invented inputs. A title never changes the classification. Existing immutable projects are not reclassified to enable maps.
3. Read the actual saved Molecule and chain IDs. Append a clearly labeled engineering numbering/material/evidence bundle referencing those IDs. CSV currently creates `chain-1`; do not assume a chain named H. The mapping is an explicit fixture input with engineering_fixture status, never a fabricated source_verified attestation or a claimed human-validated golden assignment.
4. Supply several exact CDR3 groups, two visibly different candidates, a binding assay context with source/version, a true zero, a null value with a recorded unit, unknown conditions/version, an alternate unit/context and multiple-material ambiguity. A raw binding response metric can illustrate zero without implying an actual zero-affinity measurement. All values are explicitly invented engineering fixtures.
5. Actually select context and an ambiguous observation in the browser, verify ascending/descending behavior and unavailable statuses, inspect two candidates in W, then preserve five IDs into R. Preview/save a reason with relevant source snapshots. Restart the process and compare exact IDs/reason/snapshots and restored context. The two prescribed negative names remain `e2e_j01_invalid_sequence` and `e2e_j01_missing_measurement`.

This can establish the specified **engineering J01 path** with clearly labeled fixtures under AGENTS.md. It does not satisfy the separate 18 human-validated scientific golden examples, researcher evaluation or all Release 1.0 gates.

## Independently proposed additional edges

1. **Type-aware cohort conditions:** reordered JSON object keys remain the same context, but `0` versus `false`, different array order, changed source version and case-different unit remain separate. No source value is rewritten to join them.
2. **Equal repeated samples and null:** two Materials give equal values, or one gives a value and another null. Both cases still require explicit Evidence choice. Selecting null must not fall back to the other result. A true zero sorts normally; missing/ambiguous states remain last in either direction.
3. **Stable defining ID:** append a new cohort member that sorts before the original representative, then export/reimport entities in a different order. The old selected Evidence ID still defines the same cohort; candidate selections and explicit sample choices remain unchanged.
4. **Wrong identity/stale controls:** attempt a same-sequence or parent/child candidate's Evidence ID, an outside-cohort observation, malformed falsy choices and choices without a cohort. Reject clearly without changing the database or silently replacing the chosen observation.
5. **View changes and persistence:** changing numeric context/direction/CDR group must not clear the five candidate IDs. R still exposes original incompatible/unknown records separately. localStorage contains opaque Evidence IDs and direction, not the displayed scalar/conditions/sequence payload.

## Language and terminology

Keep code and core UI labels in English. Human explanations can switch between English and Japanese without translating or normalizing stored metric names, units, conditions, source text or research notes. Switching explanation language must not alter selections, numeric interpretation or persisted scientific records.

Use **humanness** for a method-specific assessment of how human-like an antibody sequence is; it is not the engineering action **humanization**. Suitable Japanese explanations distinguish humanness (“ヒト抗体らしさ”, with the actual method definition) from humanization (“ヒト化”, an antibody-sequence engineering action). A sorting feature does not compute either one. Do not label a humanness value as “ヒト化” or imply that higher humanness proves preserved function.

## Passage boundary

No product mission, persona, four-screen architecture, external-sharing default, licensing or scientific definition changes are introduced. The explicit new-project classification control implements an existing provenance field with its existing research default; it does not require a new requester decision. F09 may proceed to independent implementation replay. Full J01 is passed only after the genuine complete fixture-based path and both prescribed negatives are executed; other journeys and final scientific/user/performance/security gates remain pending.
