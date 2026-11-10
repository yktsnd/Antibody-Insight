# Independent shortlist draft review

Reviewer: `/root/draft_entry_review`, separate from the implementation author. Date: 2026-11-10. Scope: P01/P07, J01/J07, AC-J01/AC-J07, the newly reported shortlist draft-loss defect and ownership boundaries. **PASS for this bounded engineering correction.** This report is not whole-product acceptance, scientific validation, actual-researcher evaluation, or the complete eight-journey regression gate.

The research action is retaining the candidate-selection rationale and chosen original evidence while inspecting the molecule in W and returning to R. The patch reuses volatile, project-and-candidate-set-scoped draft state and the existing immutable preview/save path. It does not introduce a new decision meaning or place private scientific text in browser storage. This is proportionate to the observed workflow interruption. Ordinary-data preparation, scientific correspondence validation and real-user first-use performance remain separate product gaps.

I inspected the charter, J01/J07 actions and ACs, traceability, latest ADR and alignment checkpoint, then ran an independent Chrome/temporary-SQLite replay from `tests/shortlist-independent-browser.cjs`. The fixture is explicitly synthetic. No existing research database was accessed or changed. Local-only browser routing recorded no external request; no page errors occurred. I also inspected the resulting screenshot.

Results: `M6-shortlist-independent-browser-v2.json`, nine checks passed. `v1.json` also passed seven checks; it was the first post-patch run, not a reproduction of the unfixed baseline. The expanded v2 contains:

- R→W→R preserves exact reason text and the excluded evidence ID; the preview contains exactly the checked IDs.
- A different candidate set has independent text/choices. Returning to the original set in reverse selection order restores the same draft.
- A separate project has independent state; returning restores the original draft.
- All evidence may remain excluded; whitespace-only reasoning cannot open a preview or write a decision.
- A submitted save freezes the exact reviewed snapshot while an edit typed during the pending request survives, including after another W roundtrip.
- A late rejected save cannot erase the revised draft or display its obsolete error over it.
- A delayed post-save bundle fetch cannot overwrite a newer project and its rationale.
- An ordinary successful save persists the exact reason/evidence snapshot and clears only that submitted draft.
- Script-looking reason text stays literal; no private draft text appears in localStorage, and no external requests/page errors occur.

The final three ownership cases exceed the reported roundtrip repro. Source inspection initially identified pending-save deletion by mutable-object identity and post-save bundle ownership as risks. I sent them to the implementer; the implementer added draft edit versions and bundle/scope checks before the actual first run. Both corrections were exercised by the replay. No production changes were made by this reviewer.

Reviewed `web/app.js` SHA-256 at the v2 checkpoint: `77dcb6b345784d4bd191ca5fa856d1a521a76244c0a6044df5da0c8625018d21`. Test SHA-256: `12319d9ff6a2e0afc0b6e768c4c4622eeebae9fe56e1c309ef9e861ec527ca85`. Later entry or production edits require replay against the final source; this report does not attest unseen edits.

Unsaved input remains deliberately volatile: closing/reloading the tab is outside this bounded persistence promise and the UI says to save before doing so. Restart persistence applies to saved immutable decisions and remains covered by the main J01 acceptance, not by a claim that in-memory drafts survive restart.

## Expanded recovery review, v3

**FAIL pending correction/replay of an additional recovery case.** The prior nine-case PASS above remains a historical bounded result. `M6-shortlist-independent-browser-v3.json` adds a forced failure of the bundle refresh after a successful shortlist write. The new immutable record exists in SQLite, but the UI silently continues displaying the previous saved-record notification/ID, because the error-owner predicate depends on a pending preview that was already cleared. The user lacks reliable confirmation of the actual save. I sent this finding to the implementer. This is an actual browser/API replay; no production edit was made by the reviewer. Preserve v3 rather than replacing it with a later pass.

## Corrected recovery and final bounded replay, v4

**PASS for the expanded ten-case correction**, closing the v3 recovery finding. The implementer separated post-save ownership from the preview state and reports the actual saved record ID before fetching the refreshed bundle. `M6-shortlist-independent-browser-v4.json` independently replays all prior cases and the forced refresh rejection, verifies the actual persisted ID is disclosed, and records unchanged before/after source byte hashes. The test file now records source hashes itself; the earlier v2 test hash above identifies that historical test version, not the expanded final test. This pass includes the app source with the paired-example/grouped-FASTA entry changes. Whole-product acceptance and the final frozen eight-journey regression remain separate. No production source was edited by this reviewer.
