# Explicit research decisions and saved versions

F19/F20 · P07/P08 · J07/J08 · AC-J07/AC-J08. [ADR-0010](../ADR/ADR-0010-evidence-based-decision-revisions.md) and its independent design review define the boundary. Domain/API review is PASS; browser and final integration acceptance remain separately pending.

The researcher's choice is recorded with original observations and trade-offs. Importance and preferences are declarations, not a biological model, composite score, ranking or recommendation. Finalized means the record is fixed; it does not validate a scientific conclusion or authenticate the researcher.

## Stored shape and compatibility

Existing awx/1 shortlists retain their exact fields/meaning: no `chosen_candidate_ids`, `source` or `hypothesis_ids`; empty criteria; draft; revision1; no predecessor. New Decisions require all three new fields whenever any is present. Nonempty criteria without those fields are invalid. Old records are never rewritten, and older application binaries may reject new fields instead of silently dropping them.

New records retain actual comparison `candidate_ids`, explicit `chosen_candidate_ids`, criteria, supporting `hypothesis_ids`, complete original Evidence snapshots, reason, entry source/application version, creation/event timestamps, status (`draft` or `finalized`), revision and `supersedes`. Drafts may have no criteria or no chosen candidate, but require a reason. Finalized records require at least one criterion and chosen candidate, with complete required observations. No score/confidence fields are supported.

Each criterion has a stable local `key`, name, explicit safe nonnegative numeric weight, boolean required flag, authored preference (`higher`, `lower`, `inspect`), original `anchor_evidence_id` and `evidence_choices` containing exactly every compared candidate key. Choices are an actual original Evidence ID or null. UI weight text is parsed on the server with existing strict JSON number handling before storage; blank, nonfinite, boolean, unsafe or underflowed values reject rather than becoming 0. Stored weights are numeric. There is no sum-to-one or positive-total requirement.

## Original observations and missingness

The anchor must belong to the actual comparison scope and pass existing F09 eligibility: measured/computed kind, known original unit/source version/assay conditions. Derive exact metric/kind/unit/typed-condition/source context from the anchor. Each chosen record must resolve through its own actual Material/Construct/Molecule/Structure path to that candidate and have exactly that context. Equal sequence, label, physical-unit equivalence or rounded value never substitutes for identity. Unknown-context, literature and annotation originals remain inspectable/citable without entering a manufactured numeric context.

No result is selected automatically, even when only one is eligible. A selected null scalar retains its actual source ID and is value-missing. An unselected cell stays unchosen; several eligible records require explicit choice. Zero is an observed value. No means, conversions, normalization, replicate assumption or missing-value replacement is performed.

Every required criterion needs an explicitly selected numeric observation for **every comparison candidate**, including unchosen candidates. Weight 0 and preference `inspect` do not waive this readiness policy. Optional missing observations remain visible even in finalized records. Researchers can explicitly revise requirements or comparison scope with a reason and visible saved-version differences; the software does not make a scientific-validity judgment or automatic waiver.

## Snapshots, revisions and API boundary

The frozen snapshot union includes every anchor, selected observation, additional supporting Evidence and related Evidence of each selected proposed Hypothesis. Each Hypothesis's entire molecule scope must be inside the comparison. Original statuses, source subjects and exact JSON numeric types/signs remain unchanged. Snapshot equality and full dependency closure are checked for direct import as well as preview/save; a proposed Hypothesis is not promoted to a fact.

Every saved version is append-only. A successor points to an actual same-project Decision, has exactly previous revision+1, and cannot share its predecessor with another successor. Legacy shortlists may have a new-contract revision2 without modifying the old record. Atomic validation of the entire combined graph inside `BEGIN IMMEDIATE` rejects reverse-order imported forks and racing/stale successors. Independent first-version decision episodes remain possible. Later Evidence never changes prior snapshots.

`POST /api/decision-context` accepts actual project/candidate IDs and returns original eligible context options and incomplete-context reasons without ranking. `POST /api/decision-review` accepts an explicit definition (candidate/chosen IDs, criteria, hypotheses, additional source IDs, reason, requested status, predecessor), derives actual revision/source/snapshots and the review table, then applies the complete graph constraints. It does not accept fabricated readiness, scores, timestamps, source metadata or client snapshots. Draft review shows finalization blockers; a finalization request with blockers rejects. The existing atomic `/api/import` revalidates reviewed records. Approved raw snapshot transport and fresh full-project export preserve original records and dependencies.

Scientific drafts stay in volatile project/scope/version-specific memory. Context readouts, preview, save and error responses must retain their actual owner across input, task, selection, project and revision changes. Original-source inspection in W and return to R preserve the draft and actual candidate set. localStorage retains only known IDs/view state. No external transmission or new runtime is introduced.

Scientific golden review, actual researcher evaluation and final J01–J08 integration/release gates remain required; engineering fixtures do not establish biological validity or practical acceptance.
