# Verification evidence

Store the input identity/checksum, target commit or exact source digest, command, runtime, reviewer, time and verdict for each verified slice. Screenshots supplement data assertions; they do not prove scientific validity.

- `M0-independent-review.md`: independent design PASS, with full M1 and release still pending.
- `M0-screen-prototype.png`: static four-screen design rendered in Chrome.
- `M1-browser-results.json`: initial F01–F05 browser replay, including actual server restart and JSON comparison; not full J01–J08 acceptance.
- `M1-evidence-screen.png`, `M1-explorer-800.png`, `M1-mobile.png`: synthetic engineering fixtures only. The Explorer image captures a viewport of the 800-row dataset.
- `M1-browser-failure.json`: first browser run's strict-locator failure, retained as debugging evidence; later run supersedes it.
- `M1-initial-independent-review.md`: implementation verdict when the independent replay is complete.
- `M1-composition-independent-review.md`, `M1-composition-independent-test-log.txt`: F06 implementation and M1 engineering-gate PASS; 104 tests and 11 browser checks. The final journey/scientific/user gates remain pending.
- `M1-composition-screen.png`: explicit declared components and lineage, not validated physical assembly.
- `M2-numbering-independent-review.md`, `M2-numbering-independent-test-log.txt`: F07 PASS; 159 Python tests and 5 numbering Chrome checks, with the full M2/journeys still pending.
- `M2-retained-foundation-browser-review.json`: all 11 retained browser assertions passed, followed by a OneDrive/Windows result-write error; the original nonzero exit and results are retained transparently.
- `M2-numbering-screen.png`, `M2-numbering-explorer.png`: synthetic imported maps and complete CDR-H3 groups. They are not human-validated scientific golden data.
- `M2-structure-independent-review.md`, `M2-structure-independent-test-log.txt`: F08 PASS; 207 Python tests and11/5/11 Chrome checks with actual PDB/mmCIF atom clicks, physical rotation/wheel zoom, manual correspondence, missing-source handling, project isolation and restart/roundtrip. All exit0. Full M2 and final journeys remain pending.
- `M2-structure-screen.png`: actual local WebGL rendering of synthetic coordinates, with source/model/chain roles and internal computed metrics explicitly labeled.

The prescribed eight journeys and sixteen negatives remain separate final acceptance items. An unsupported-structure rejection in the foundation is not a successful complete J08 structure-import journey.

F09 / J01 / M2 engineering: independent PASS in `M2-observation-independent-review.md`, with 252 Python tests and 11/5/11/5 Chrome checks plus three independently added asynchronous-race checks. `M2-observation-independent-J01-results.json` contains the named full J01 main and its two prescribed negatives. `JOURNEY_ACCEPTANCE.json` binds the reviewer, exact artifact hashes, reviewed source manifest and implementation commit; at that registration the checker validated 1/8 journeys and 2/16 prescribed negatives. Seven journeys were pending at that stage; the latest M3 registration is recorded below.

The original full runtime digest is preserved in `M2-observation-independent-runtime-replay-source-manifest.json`. Only the requester-authorized AGENTS documentation changed afterward; the reviewer inspected that delta and verified every runtime/test/script digest unchanged in the final source manifest. The bilingual product-alignment documents were reviewed separately.

`J01-browser-failure.json` preserves the first harness assertion that mistakenly matched the unit substring in the UI key chainMaps; its corrected ID/value assertion and final independent replay pass. `M2-structure-browser-failure.json` preserves the asynchronous saved-viewer/detached-DOM failure; explicit reload disposal/inert content and waiting for the actual saved map revision fixed it, with all physical canvas assertions retained.

F10/F11 / J02: `M3-numbered-design-independent-review.md` records implementation, complete synthetic J02, current J01 regression and scientific-UX/mission PASS. Final replay: 297 Python tests and46 browser checks (11/5/11/5/4/3/4/3), all exit0. At the F10/F11 registration, fresh independently named J01/J02 reports and the M3 source manifest bound the acceptance entries to implementation commit `8b61d7154268217fc3a80c5060bbdcd6c5eb5297`; the checker validated 2/8 journeys and4/16 prescribed negatives at that stage. The latest F12/F13 registration is below. M2 review/manifests are retained as historical evidence.

The pre-save-fix replay is explicitly preserved in `M3-numbered-design-before-save-fix-*` and is not final acceptance. Independent regressions exposed wrong model/correspondence scope, late hypothesis previews and late save callbacks clearing newer drafts; focused regressions and the entire suite passed after correction. The native disabled-option helper diagnosis and dynamic-checkbox harness correction are distinguished from product defects in the review and `M3-J02-harness-investigation.md`.

Scientific UX references and reuse-versus-build decisions are recorded in docs/SCIENTIFIC_UX.md. These are official-document comparisons plus independent workflow inspection, not actual researcher evaluation or human scientific golden validation. At that F10/F11 stage, full M3/J03/J04/J05/J06/Release1.0 remained pending. The latest F12/F13 registration below supersedes the J03/J04 engineering status.


F12/F13 / J03/J04: `M3-observation-implementation-independent-review.md` records frozen-source implementation, science/UX and current full synthetic J01–J04 engineering PASS. Independent320 Python tests and the combined57 browser checks passed; fresh named J01/J02/J03/J04 results and source manifest bind acceptance to implementation commit `983342a280b3580a9d8eaaa449034f96f150203c`. Current engineering acceptance is4/8 journeys and8/16 prescribed negatives. Full M3/J05–J08, scientific goldens, actual researcher evaluation and final quality gates remain open.

The independent stale hypothesis-opening reproduction is retained in `M3-observation-before-intent-guard-independent-failure.json`; exact invocation-context guards fixed it and the retained regression passes. `M3-observation-before-preview-wait-browser-failure.json` preserves the initial parent test reading the previous hidden design preview before asynchronous hypothesis completion; waiting for the actual visible preview corrected the harness without weakening assertions. Public experimental1MLC source/scale evidence is separate from synthetic confidence/assay journeys. Its raw hash, licensing and byte-preservation attributes are pinned. Historical M1/M2/M3-numbered artifacts are retained byte-for-byte; fresh retained output uses the M3-observation-final-retained prefix.
