# F16/F17/F18 independent browser and scientific-UX review

Verdict: **PASS for the bounded J06 browser/UI implementation reviewed here.** Frozen-source integration, retained J01–J05 regressions and full J08 remain **NEEDS-EVIDENCE**. This report does not change registered journey counts or complete M4/the product.

Reviewer: `/root/observation_review`, separate from the implementation agent. Date: 2026-11-04 JST. Trace: F16/F17/F18; P06/P08; J06/J08; AC-J06/AC-J08. Reviewer changes were tests/evidence only. Domain/API/scientific validation is separately recorded by another reviewer in `M4-measurements-domain-independent-review.md`.

The affected research question is what recorded construct changes and original experimental observations should motivate the next controlled expression comparison. Inputs are an actual declared Molecule, independently identified Constructs and Materials/lots, canonical measurement CSV, explicit sample mappings and experimental source metadata. Outputs are reviewed new records, source-linked comparisons and a proposed next-experiment Hypothesis. Molecule/Construct/Material/Evidence/Hypothesis identities remain distinct. Translation validation, inferred CDS-to-chain association, signal processing, expression prediction, causal effects, statistical pooling and finalized scientific decisions are outside this implementation.

## Independent replay

Executed with the repository Python environment, Chrome/Playwright and temporary databases, using clearly labelled synthetic observations only:

- `node tests/j06-browser.cjs`: **4 PASS**, independently executed here. Actual UI registration of two Constructs and three Materials, file-scoped measurement mapping/QC, D recorded differences, W actual paths, R original observations and proposed controlled next question, actual server restart and native export/fresh-database reimport. Both prescribed AC-J06 negatives pass. The fresh-roundtrip check compares canonical typed JSON using Python, rather than JavaScript equality.
- `node tests/experiments-independent-browser.cjs`: **8 PASS**, independently proposed and implemented here. Actual native inputs/buttons, intercepted request timing and a delayed actual File read exercise ownership rather than calling application callbacks directly.

Raw reports/logs: `M4-J06-independent-browser-results.json`, `M4-J06-independent-replay-run.log`, `M4-experiments-independent-browser-results.json`, `M4-experiments-independent-browser-run.log`. Independently replayed D/R screenshots: `M4-J06-independent-construct-comparison.png` and `M4-J06-independent-material-observations.png`. The bounded reviewed file hashes are in `M4-experiments-ui-reviewed-files.json`; this is not a whole-source freeze.

The named J06 replay initially assumed a cohort's first-created Evidence ID was its native dropdown representative. Representatives are lexicographically chosen actual members. The test now selects the actual metric/unit option and retains the original two-row assertion. My added cohort edge initially retained a right-Construct filter from an earlier scenario; it now explicitly clears both comparison inputs before asserting all-Material coverage. These harness corrections changed no product contract.

## Independently added boundaries

1. Delayed D/R context reads preserve metadata and shortlist text entered while loading; only asynchronous readout regions update.
2. A late metadata preview cannot open after a newer text edit or project change, or replace another project's draft. Drafts remain associated with their actual project/Molecule.
3. An old rejected metadata save cannot enable a newer in-flight Save button or inject its error into the newer modal. Only the actual approved current record saves.
4. A successful metadata save submitted in the original project cannot switch back from another project, erase its newer draft or add records there.
5. `__proto__` maps to the explicitly chosen actual Material, with no prototype-key interpretation. Replacing the input with `constructor` loses the earlier mapping; unresolved rows stay unsaveable. A current invalid UTF-8 file clears the prior text and cannot save it.
6. Delayed measurement previews cannot replace newer file text or reopen a closed dialog after a project switch. No write occurs in these rejected/stale review paths.
7. Adding a lower-ID member to a selected exact observation context preserves all three original-subject rows and the selected context after actual reload. The unknown-context observation remains outside that context until All is selected; its unknown value/conditions remain visible then.
8. A delayed failed read of an older invalid file cannot overwrite the current notification or insert an error into a newer valid, saveable preview. No scientific draft, CSV token or sequence was found in localStorage; no browser error or outbound request occurred in the suite.

## Finding and correction

The eighth boundary initially **failed**: the old File read's UTF-8 decode exception was unconditionally reported after a newer valid file reached preview. It replaced the current notification and injected an obsolete dialog error. Initial reproductions are preserved as `M4-experiments-independent-before-file-ownership-fix-results.json` and `M4-experiments-independent-before-file-ownership-fix-run.log`.

The implementation agent now checks the exact import epoch, selected File and open dialog before reporting decode/read failures. Current invalid input still clears prior text, pending review and mappings. New imports and current successful previews clear their previous local error; metadata review likewise clears its old local error. The complete eight-case independent suite passed after these changes. No data corruption was observed in the reproduction, and no unresolved P0/P1 was identified in this bounded reviewed scope.

## Scientific usefulness and remaining gates

The researcher can now distinguish two declared expression constructs for the same protein, inspect the recorded CDS/vector/signal differences without an inferred biological interpretation, follow actual lots and original result IDs, and retain a question for a controlled experiment. Original units/conditions/sources and missingness remain visible; matching metadata is explicitly insufficient to establish comparability. Raw DNA indexes are distinguished from amino-acid positions. Source provenance describes the actual entry/import mechanism separately from the experiment and does not authenticate an absent original file.

The implementation preserves E/W/D/R and reuses native entity selectors, progressive details, existing preview/save, source-linked tables and proposed hypotheses. The documented Benchling/Skyline/two-input sequence comparison benchmark supports these familiar interactions. A general ETL system, new alignment engine, translation validator or dashboard would add complexity without resolving this bounded identity/provenance problem better. The table repeats presentation of original records while source cards retain their identity; the retained test correctly scopes original Evidence-card counts to `.evidence-row`, preserving its original measured/computed assertions.

The largest immediate acceptance gap is the unperformed frozen-source integration replay. J07 finalized decisions/revisions, complete J08 adapters/reproducibility, scientific reference validation, actual researcher evaluation and release gates remain open. Synthetic engineering success establishes the coherent operation tested here, not scientific or practical acceptance by researchers.
