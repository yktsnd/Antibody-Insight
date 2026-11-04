# M5 original-source detail: independent bounded correction review

Verdict: **PASS for the lazy source-metadata and existing-ID-index correction only.** Final frozen actual-browser J01–J08 acceptance remains pending. Reviewer `/root/m5_integration_review`, separate from implementation;2026-11-05 Asia/Tokyo. Trace: F21/F22, P03/P08, J03/J08, AC-J03/AC-J08.

## Finding and bounded change

Independent inspection found that each W/R source-backed Evidence detail included its source's complete allocation table in initial HTML. Deferring raw JSON alone did not prevent quadratic metadata expansion. A source can legitimately contain1000 scalar records in one project well below32MiB, yet every scalar repeated1000 allocations. The implementation now leaves both original-content and metadata pre elements empty, populates only the chosen native detail on open using textContent, and clears that detail on close. It also reuses the application's existing ID index for exact source/optional coordinate lookups, toggle and download, rather than adding another cache or repeatedly scanning source-last imports. Canonical sources do not look up an absent structure ID. No source or scientific value is edited, no identity/scope changes and no new screen/network action is added.

For an exact before comparison I reconstructed the two previous renderer hunks from the observed source and verified the resulting **entire file SHA-256 against the separate earlier UI review**: `b987785e0ffcad6d6a37f97e140ab57273590b4b03e1fc7aef6603501a1d7cde`. The exact verified snapshot is M5-integration-independent-reviewed-pre-lazy-metadata.js. This is not an invented representative implementation. Both that reviewed renderer and the actual corrected renderer were executed on the same real domain-validated synthetic canonical import.

The valid1000-value project is1,231,433 UTF-8 bytes; its original BOM/CRLF JSON is397,057 bytes. Initial source-detail HTML fell from **162,153,890** characters to **1,122,890**. Both models retain the actual direct subject, source ID and JSON pointer; the correction changes presentation/allocation, not provenance or scientific interpretation. A separate pre-index source-last review probe recorded10000 origin calls taking about5.24s without DOM work; that probe is evidence of the repeated lookup mechanism, not a standard-host performance gate. The post-correction independent edge forbids entity-list scans while retaining every actual allocation ID.

## Independent replay

Command: `node tests/prediction-source-details-independent.cjs`.

Result: **7/7 groups PASS** in M5-source-details-independent-results.json. Current predictions.js SHA-256 `1c344752905b786efa1c2d1cc4df57ccad0ecd63e3731ead44715766f566bf0b` and test SHA-256 `99dcc1615efbfa6971c7cac7217bd4996f45eafb32bc2aa9e9ea7c8776137700` remained stable during the replay.

1. Actual prediction_preview→validate_graph→validate_transport_size accepts the labelled1000-record source below the original limit; all1000 allocations and original BOM/CRLF remain.
2. The byte-exact earlier reviewed renderer reproduces metadata amplification on that same valid source; the corrected renderer avoids it.
3. One-record and1000-record source details have effectively the same initial per-Evidence markup. Both raw and metadata pre elements are empty; the final allocation's Evidence ID and hostile token do not enter initial markup.
4. Opening raw and metadata separately executes the actual captured native toggle handler. Complete bindings/options/all1000 actual pointer→Evidence allocations remain available. A hostile HTML-like token is written through textContent; a mock innerHTML setter throws if used. Raw text stays exact and separate from metadata.
5. Closing either detail clears only its own text, and reopening retrieves the exact source. Complete bundle records remain unchanged.
6. A source-last order with an entity-list find method that throws still renders all1000 source associations and opens complete metadata through the existing ID index. A wrong-type Evidence ID cannot trigger a source download.
7. Changing the active project and then opening stale source detail nodes shows Source unavailable; it never discloses the previous project's content.

These are actual-domain/actual-renderer Node VM checks with a controlled text sink, **not an actual-browser or operating-system performance acceptance claim**. Final frozen browser replay must still exercise genuine native details/download and the combined app selection/server changes.

## Gates, incidents and product alignment

Identity/provenance remain the same actual IDs, source pointers, allocations and raw content; only on-demand display and lookup changed. No writes or external traffic occur in this independent VM replay. The small initial test runner used an interpreted JavaScript template for Python CRLF syntax and failed before exercising product code; switching the test's Python code string to String.raw corrected that runner. An earlier valid-fixture probe hit the Node child-output buffer, so its review-runner maxBuffer was increased. Neither is a product correction. One in-progress measurement ran after the implementation had already applied the fix; that artifact is explicitly marked post-fix and is not used as before evidence. The exact verified historical snapshot supplies the before comparison.

The change supports P03/P08's freedom to inspect retained scientific sources without making normal W/R entry expand the same metadata quadratically. Reusing native details and the existing identity index is simpler than a new source browser, service or cache. The largest remaining product gap is final frozen integration/registration and the separate scientific goldens, actual researcher evaluation and specified standard-hardware release gates. This bounded PASS closes the reported source-detail defect; it does not turn synthetic fixture counts into scientific usefulness or complete the release.
