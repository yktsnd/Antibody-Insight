# F16-F18 / J06 final engineering integration review

Verdict: **PASS for J06 engineering integration with retained J01-J05 and their prescribed negatives on the recorded source.** This supports registering **6/8 main journeys and 12/16 prescribed negative flows** as engineering passes. **M4 as a whole, J07, full J08, scientific validation, actual researcher evaluation and Release 1.0 remain unfinished.**

Final reviewer: `/root/j06_design_review`, separate from the implementation agent. Date: 2026-11-04, Asia/Tokyo. Review handoff: `/root/observation_review` independently completed the bounded browser review, added eight edges, and began final integration before its resource limit. This reviewer completed the remaining final replay and assessed the combined evidence. No product or test source was edited during this final replay. Trace: F16/F17/F18; P06/P08; J06/J08; AC-J06/AC-J08, with retained P01-P05 / J01-J05 / their ACs.

## Source identity and execution ownership

Final source identity: **`cac62fd78d9bf39761945599468e21f47d8295d0e423100d8ca57320e351ade0`**, 84 files. Implementation freeze: `M4-experiments-final-freeze-source-manifest.json`. This reviewer independently generated `M4-experiments-independent-final-source-manifest.json`, verified the matching aggregate, and checked every actual file hash before replay, after each of eight suites, and after completion. All 84 matched.

The initial integration freeze was `9d8a66d735ed42be73156e99a5c566e21d7491ded814738276d54b82712c3280`. Its only changed source file in the final freeze is `tests/observation-journeys-browser.cjs`: the failure handler now records URL, notification, breadcrumb and readiness details. Tested operations and runtime product source are unchanged. This supports retaining completed checks on the initial freeze while independently rerunning the affected script on the final freeze. No claim is made that both manifests are byte-identical.

Execution and evidence ownership are explicit:

| Verification | Executed by | Independently assessed result |
|---|---|---|
| Full Python suite, initial integration freeze | Implementation agent and `/root/observation_review`, separate runs | **412 PASS** in each run; `M4-experiments-final-python.log` and `M4-experiments-independent-python.log` |
| Retained foundation/numbering/structures/observation-race/hypothesis/save browser suites | Implementation agent on initial freeze; raw logs inspected by this reviewer | **37 checks PASS** across six scripts; `M4-experiments-final-retained-*.log` |
| J01 and J02 complete journeys plus prescribed negatives | `/root/observation_review` on initial freeze; logs/results inspected by this reviewer | **5 and 4 groups PASS**; `M4-experiments-independent-J01-*` and `-J02-*` |
| J03/J04/public source-scale; J05; J06; representation; composition; new experiments; numeric transport; numeric guards | **This reviewer on final freeze**, actual browsers and temporary local servers/databases | **All eight suites exit 0 / PASS**, fresh final-prefixed evidence |

The 37 retained checks are 11 foundation, 5 numbering, 11 structures, 3 observation ownership, 4 hypothesis ownership and 3 pending-save ownership checks. This reviewer inspected their actual log contents and the checked behaviors, rather than counting filenames. Full Python was not needlessly repeated after the diagnostic-only JavaScript test change. Results are engineering evidence using labelled synthetic fixtures; the separate public experimental 1MLC check establishes source/scale observation only.

## Final independent browser replay

Environment: repository Python 3.12.10, installed Chrome/Playwright, existing `NODE_PATH=C:\Users\yukis\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules`, `PYTHON` set to the repository `.venv/Scripts/python.exe`. No dependency was installed. Each command is `node tests/<script>`:

| Script | Result | Fresh result artifact under `TEST_EVIDENCE/` |
|---|---|---|
| `observation-journeys-browser.cjs` | J03 3, J04 3, public source-scale 1 PASS | `M4-experiments-independent-final-J03-results.json`, `-J04-results.json`, `-public-results.json` |
| `j05-browser.cjs` | 4 PASS | `M4-experiments-independent-final-J05-results.json` |
| `j06-browser.cjs` | 4 PASS | `M4-experiments-independent-final-J06-results.json` |
| `observation-representation-independent-browser.cjs` | 4 PASS | `M4-experiments-independent-final-representation-results.json` |
| `composition-independent-browser.cjs` | 6 PASS | `M4-experiments-independent-final-composition-results.json` |
| `experiments-independent-browser.cjs` | 8 PASS | `M4-experiments-independent-final-experiments-results.json` |
| `numeric-transport-browser.cjs` | Full typed import/export/reimport path PASS | `M4-experiments-independent-final-numeric-results.json` |
| `numeric-transport-guards-browser.cjs` | 4 PASS | `M4-experiments-independent-final-numeric-guards-results.json` |

Exact commands, exit codes, durations and paired result files are in `M4-experiments-independent-final-replay-summary.json`. Each script has a `M4-experiments-independent-final-<suite>-run.log`. Copied D/R screenshots and relevant J03/J04/J05/public screenshots share the final prefix. Evidence hashes are recorded in `M4-experiments-final-independent-evidence-sha256.json`. Historical generic output restoration is left to the implementation agent after these fresh copies; old-stage evidence must not be silently replaced by this replay.

## Coherent research action and mandatory gates

The J06 action was personally replayed here through actual controls: import an actual declared Molecule → register two distinct Constructs for that same Molecule, with different recorded CDS/signal metadata → register three distinct Materials/lots, despite repeated display names → review CSV QC and explicitly map external tokens, including `__proto__` → save original measured Evidence → compare the actual Constructs in D → follow actual Material paths in W → inspect original observations in R → save a proposed explanation, limitations and controlled next experiment → restart the actual server → native export and file reimport into a second database. Python canonical JSON verifies exact typed roundtrip. Source IDs, evidence kinds and import origins remain inspectable. I also inspected the independently generated D/R screenshots for displayed identity, units, missingness and the saved proposed question.

- **Identity: PASS.** Distinct Construct/Material IDs survive repeated names and restart. Unknown sample and canonical Molecule references cannot attach measured data to a candidate or another sample. Equal-sequence inference, inferred translation/chain pairing, synonymous-mutation claims and measured parent-to-child copying are absent. Raw one-based DNA positions remain distinct from amino-acid indexes; unknown CDS is unavailable rather than identical.
- **Provenance: PASS.** Original subject, event time, experimental source/version, unit and typed conditions persist separately from importer and submitted-text file/ref/record/line metadata. Row provenance does not split an otherwise identical assay context. Measured, computed, literature and annotation kinds retain their meanings. Unknown conditions/version and censored/null values do not acquire invented values or confidence. Repeated records are separate, without establishing independent biological replicates. Matching metadata is explicitly insufficient to establish scientific comparability.
- **Security: PASS in the tested local scope.** Strict session/Origin/CSRF/schema checks and atomic import remain. Wrong-project references and malformed encoding reject without writes. Hostile input remains text; no scientific drafts or sample tokens are stored in localStorage in the affected browser edges. The suites that explicitly track outbound requests and browser errors report none. No proprietary data was used or transmitted. Local execution is not a shared-server security or production-deployment certification.
- **Regression: PASS for the combined engineering scope above.** Prescribed J01-J06 main/negative flows remain established, including actual persisted results, source-coordinate handling, unknown confidence, unlike units and unknown assay conditions. Current checks retain old source identities and snapshots. The retained envelope assertion was independently updated only for the previously reviewed `serialized_bundle` companion, adding type-aware content fidelity checks; scientific/security assertions were preserved (`M4-assembly-envelope-contract-independent-note.md`).

The separate bounded reviews remain part of this conclusion: `M4-constructs-design-independent-review.md`, `M4-measurements-domain-independent-review.md`, `M4-experiments-ui-independent-review.md` and `M4-numeric-transport-independent-review.md`. The domain review added seven independent cases; the UI reviewer added eight meaningful edges and found/followed the stale file-read error correction. This final reviewer reran all eight UI edges, including late failures/previews/saves and changed file/project ownership. No unresolved P0/P1 defect was identified in the reviewed scope; this is not a project-wide defect-free claim.

## Recorded incidents and practical limitations

The first final attempt by the previous independent reviewer passed the first two J03 cases, then timed out while a fresh workspace's Import button remained disabled. Browser error/outbound lists were empty. The original evidence is preserved in `M4-experiments-independent-J03-J04-public-run.log` and `M4-experiments-independent-startup-before-diagnostic-failure.json`. The implementation agent added failure diagnostics only; its complete seven-group replay passed. This reviewer's independent final seven-group replay also passed. **The incident is unreproduced; its cause is unknown, and no product fix is claimed.** Do not present those successful retries as a diagnosed correction. Retain the new diagnostic handler and reopen investigation if the startup symptom recurs.

This reviewer's first command failed before launching the application because the child shell lacked the existing Playwright module path. `M4-experiments-independent-final-harness-dependency-setup.log` records this harness setup issue. Reusing the already installed dependency path resolved it; no source/dependency change occurred.

The earlier numerical representation defect is a separate, reproduced issue with independent correction evidence. The documentation now correctly states that future reviewed transfers preserve integral-float/signed-zero representations, while older records/files that have already lost those representations cannot be reconstructed without original sources. `CHANGELOG.md` and `KNOWN_LIMITATIONS.md` L14 were inspected: no automatic historical research-database rewrite or invented recovery is promised. Their documentation-only update lies outside the 84-file runtime/test source manifest.

## Mission alignment and integration boundary

P06 can now ask which recorded construct differences and original expression/quality observations justify a controlled comparison, inspect those records and retain the next experiment without receiving an unsupported causal answer. P08 gains faithful identity/provenance/typed-data transfer. Native selectors, linked source tables, exact existing observation contexts and proposed hypotheses complete this action with less complexity than a new alignment, translation, prediction or statistical engine. The documented Benchling/Skyline/two-input comparison references support familiar scientific interaction; no third-party code or service was introduced for this action.

The largest remaining product barrier is **J07's researcher-defined final criteria, missing-data controls and immutable decision revisions**, followed by complete J08 adapters/reproducibility. The ADR-0010 draft is planning material and is not implemented or accepted by this report. Scientific golden validation, evaluation by the eight actual researcher roles, coverage/performance/storage/security release gates and final Release 1.0 remain open. The final-eight-workflow goal is unchanged. Integrating J06 is justified; declaring the whole M4 milestone or product complete is not.
