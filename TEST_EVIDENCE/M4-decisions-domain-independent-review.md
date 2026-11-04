# F19/F20 decision domain/API independent review

Verdict: **PASS for the bounded domain/API implementation at the scoped file hashes recorded below.** No product defect was found in this review. This is not J07 browser acceptance, complete M4, J08 acceptance or Release 1.0 approval.

Reviewer: `/root/decision_design_review`, independent of implementation. Recorded 2026-11-04 19:01 Asia/Tokyo. Working tree based on `76a9f29e8adec4695d244dceaca58e0180936a8d`; J07 changes were uncommitted. The existing accepted J01–J06 product-source baseline remains separately identified as `2c2a96ffe67dc58ab8110b72c839a3948288a914`. Scoped SHA256 hashes, including the actual API source and tests, are in [the manifest](M4-decisions-domain-independent-manifest.json). Files changed later require review proportional to their change; this report does not approve future source.

## Research action and scope

Trace: F19 / P07 / J07 / AC-J07 for explicit criteria, exact observations and missing-required controls; F20 / P07/P08 / J07/J08 / AC-J07/AC-J08 for immutable versions, snapshots and reproducibility.

The researcher compares actual candidates and original observations, declares importance and preferences, records a chosen subset and reason, saves a draft or finalized immutable version, then creates an explicit successor when judgment changes. Input entities keep Molecule/Construct/Material/Structure/Hypothesis identities distinct. Output is a retained Decision with its original Evidence union, chosen subset, declared criteria, source, timestamps and predecessor; weights are not a model or score.

This review independently reread ADR-0010's clarified validation boundary and the approved design review, inspected `decisions.py`, the Decision branches/reference integration in `domain.py`, the new server routes and existing append-only storage/context/hypothesis/strict-JSON mechanisms. The previously read charter, original J07/J08 AC/negatives and English/Japanese alignment checkpoint remain the governing product scope. Product implementation was not edited by this reviewer. Changes made here are the independent test file, actual test log, hash manifest and this report. No broad regression rerun or research-database mutation was performed.

## Execution evidence

Command: `python -m pytest tests/test_decisions.py tests/test_decisions_independent.py -q -rA`

Result: **40 passed in 3.03s; exit 0**, comprising 32 implementation tests and 8 independently added cases. Full captured results are in [the test log](M4-decisions-domain-independent-tests.log). Independent cases are in `tests/test_decisions_independent.py`. Temporary isolated SQLite databases and localhost test servers used clearly labeled synthetic fixtures; there was no external service or proprietary data transmission.

Confirmed from source plus execution:

- Actual comparison/choice identity, exact measured/computed context, typed conditions/source versions and complete candidate-keyed choices are revalidated. A sole available observation is not silently chosen. Null choice, selected null scalar and numeric zero remain distinct.
- Required criteria apply to every compared candidate, including unchosen candidates and weight0 criteria. Finalization rejects unresolved required observations; draft preview returns blockers. Optional missing values can remain explicitly missing in a finalized decision. No composite score, normalization or recommendation is computed.
- Legacy empty-criteria revision1 drafts retain their original shape and behavior. A new-field presence invokes the complete new shape; new draft incompleteness does not waive reference/snapshot validity. A legacy record can be superseded without being rewritten.
- Frozen snapshots contain anchors, choices, supporting sources and referenced hypotheses' related Evidence; strict equality to original records is enforced for direct imports. Hypothesis scope remains explicit and proposed. Exact source records, original Material/lot relationships, integer/float distinctions and signed zero survive persistence/fresh transfer.
- Predecessors must be real same-project Decisions, revision increments are exact and single-successor checks run inside the existing serialized import transaction. Reverse-order full-chain import is valid; forks/racing successors reject rather than overwrite. Earlier records remain unchanged after new Evidence is added.
- New POST routes inherit Host/session/Origin/CSRF and strict request-field checks. Preview performs no write; `/api/import` revalidates the actual record. Duplicate JSON keys, underflow, forged readiness input and invalid predecessors cannot bypass server checks.

## Independently proposed and executed edges

1. **Mixed atomic batch with invalid predecessor (3 cases).** Import otherwise valid additional Evidence with a Decision pointing to an unknown Decision, an Evidence ID, or itself. Each import rejects, and an independently reopened database matches the complete pre-import bundle. No valid leading entity leaks through a rejected batch.
2. **Null anchor versus explicitly selected alternate-lot negative zero.** The original eligible context anchor has a null scalar; an explicit source from another actual lot has `-0.0`. The selected source satisfies presence without promoting the anchor's missing value or changing either subject. Both originals are frozen; exact canonical record equality and signed zero survive restart/export/fresh import.
3. **Boolean and float condition mismatches (2 cases).** An anchor's condition metadata uses integer1; a selected observation uses boolean true or float1.0. Both reject even in draft despite Python's ordinary numerical equality, proving the exact typed context boundary is enforced.
4. **Legacy-looking draft with incomplete new snapshot closure.** Copy an old shortlist, add all new fields/criteria but omit the other actual criterion observations from its snapshot. Direct import rejects as incomplete, and the existing legacy record/database remain unchanged. A draft cannot use the legacy branch as a validation escape.
5. **Raw HTTP malformed scientific request.** Send a duplicated candidate-choice JSON key, weight text `1e-9999`, and a wrong-kind predecessor to the actual review endpoint with a valid local session. Every request returns422; the separately reopened database remains identical. Blank/underflow handling is not a client-only convenience.

The implementation tests additionally exercised the happy three-candidate/three-criterion record, all-comparison missing-required policy, optional missingness, hypothesis dependency closure, context eligibility/mismatch, legacy successor, reverse-order imported fork, concurrent save race, exact fresh roundtrip and actual HTTP strict-save validation.

## Gates and product alignment

Identity: PASS for this domain/API scope. Original Material measurements remain attached to their actual subjects; equal sequences never authorize cross-candidate assignment.

Provenance: PASS for this scope. Original snapshots, declared criteria/weights, local-entry mechanism/version and predecessor history are retained; imported source metadata is not authenticated human authorship.

Security: PASS for the reviewed API boundary and executed negative inputs. This does not substitute for final whole-product security/storage/network evidence or browser rendering and draft-persistence tests.

Regression: legacy shortlist compatibility and targeted existing-domain mechanisms used by the decision tests pass. Broad J01–J06 browser regression was intentionally not repeated before the final freeze and remains a full-integration gate. No existing test was removed or weakened.

The implementation directly supports P07's question, “why choose this candidate?”, and P08's ability to reconstruct that decision. Native explicit tables/source choices and append-only versions reuse existing IDs and storage without adding scientific assumptions. A new scoring engine, waiver framework or prediction model would not serve this action better. The largest remaining product obstacle is the complete J07 E→R→W→R user action: draft ownership across navigation/async operations, original-source inspection, visible version differences, explicit review/save/export and actual restart/reimport must still be independently replayed in the browser. Complete J08, human scientific goldens, actual researcher evaluation and all release gates remain open. Passing these 40 engineering cases does not establish scientific utility or biological validity.
