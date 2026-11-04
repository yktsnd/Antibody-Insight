# Explorer native selection correction: independent review

Verdict: **PASS for the bounded selection-behavior correction.** This is a functional review, not a latency, standard-hardware or release qualification. Final integrated eight-journey replay remains pending.

Reviewer: `/root/j06_design_review`, separate from implementation. Recorded2026-11-05, Asia/Tokyo. Trace: existing F02, P01/P08, J01/J08, AC-J01/AC-J08. Reviewer changes were the independent test and new evidence only; no product or active acceptance metadata was edited.

The researcher selects/unselects an actual Molecule checkbox in E. The correction reuses the existing native table/checkbox and selected-context controls, updating counts, selected-row class and context links without rebuilding the entire table. It changes no research entity, scientific definition, sorting/observation policy, candidate visibility, primary screen or data-sharing policy. It is required quality work following the separately recorded interaction diagnosis, not a discretionary selection feature.

## Inspection and actual replay

Reviewed `docs/SELECTION_LATENCY_REVIEW.md`, the two existing-context render/update helpers, initial count/context markup and the actual checkbox change handler in app.js. The helper calls the existing ID/view-state persistence, updates both counts and the current row, and uses the same context-strip renderer as full E rendering. Filtering, navigation and project reload retain their normal full-render paths. No scientific data or original observation choice is reset.

Command: `node tests/selection-independent-browser.cjs` → **2 groups PASS, exit0**. Evidence: `M5-selection-independent-browser-results.json`, `M5-selection-independent-browser-run.log`, `M5-selection-independent-state.png`. The independent fixture has1000 distinct actual Molecule IDs, deliberately repeated sequences, real declared binding-observation alternatives on distinct Materials, and a fully reidentified second project. Everything is labelled synthetic; no actual experiment or private research database was used.

1. **Hidden selection, focus and original choice.** Explicitly choose an alternative original binding Evidence, select the first actual candidate, filter it out, then select a different candidate. Both selected IDs/counts survive clearing the filter. The checkbox/row and observation-select DOM nodes remain identical after the bounded update, with native focus retained. All1000 rows remain present after clearing the filter. Existing context links reach W/R with the same two IDs; returning to E retains the exact chosen original Evidence.
2. **Project/reload and last unselect.** The second project starts without the first project's selection or observation context. Its separate selection persists while switching back. The first project's two IDs, exact context and chosen Evidence survive actual reload. Unselecting both, including the last candidate, retains native checkbox/row/observation-control identity/focus, clears both counts and context links, removes selected-row classes, and leaves all1000 candidates and the original observation choice/context intact. Another reload retains that zero selection and original choice; the second project's independent selection remains. Canonical Python digests of both saved scientific graphs are identical to their pre-interaction values. No private scientific content appeared in localStorage, no outbound request occurred and no browser error was observed.

## Timing and source boundary

These cases intentionally contain no elapsed-time assertion. The root host-performance run briefly overlapped this functional replay; the implementation agent was notified immediately and is preserving/repeating its measurements rather than treating overlap as qualified performance evidence. The functional assertions passed and make no claim about that timing run. The standard16GB/SSD performance criterion cannot be certified from this host-only functional review.

The reviewed selection helpers remained unchanged throughout. A separate concurrent app.js configuration change delegates PredictionUI's file lookup to the existing entity-ID index; prediction metadata lazy loading/lookup performance is handled by the separate prediction reviewer and is **not approved by this selection report**. The manifest records the helper fragment/handler hashes and current observed app dependency separately. The original prediction-UI report remains bound to its pre-selection snapshot and is not rewritten to imply a combined replay.

## Gates, usefulness and remaining work

Identity/provenance pass in this scope: equal sequences remain different IDs; hidden rows do not erase selected candidates; declared original Evidence choices are not replaced; project/view persistence contains IDs rather than source values; stored research records remain exactly unchanged. Security/privacy checks found no scientific-data storage or network regression. No product defect or unresolved P0/P1 was found in these two cases. The root's separate full J01 replay is supporting evidence, not a personally executed result claimed here; retained J01-J08 integration must still run on the final combined source.

Keeping the native focused checkbox and existing table is a simpler correction than virtualization, pagination, hidden candidates or a new selection component. It supports P01/P08's actual comparison action without adding scientific assumptions or incidental controls. This bounded PASS permits proceeding to uncontaminated host measurements and final freeze; it does not advance registered workflow counts or complete the scientific/user/release gates.

Scoped source/fragment/test and evidence hashes: `M5-selection-ui-reviewed-files.json`.
