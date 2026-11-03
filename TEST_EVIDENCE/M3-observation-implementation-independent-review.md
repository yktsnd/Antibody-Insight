# F12/F13 observation-to-hypothesis independent implementation review

Verdict: **PASS for the reviewed F12/F13 engineering milestone and current complete synthetic J01–J04 paths.**
Full M3, J05–J08, scientific golden validation, actual researcher evaluation and Release 1.0: **NEEDS-EVIDENCE**.

Reviewer: `/root/observation_review`, independent of the implementation agent. Date: 2026-11-03, Asia/Tokyo.
Reviewed frozen source SHA-256: `36f338e4ab813ebfcf12b2ca680e24cd993eb8c042a1a6e6cc1ea1db97d335c3`.
Baseline Git commit: `c834094b96eaf4d04aefefd04ed20a900c8afe13`; the exact tested working-tree files are pinned by `M3-observation-independent-source-manifest.json`. The source inventory and every file digest were checked again after replay: no changes. Registration against the eventual implementation commit is a separate verification step; this report does not manufacture a commit ID or finalize the product.

## Research action and scientific scope

Trace: F12/F13, P03/P04, J03/J04, AC-J03/AC-J04. Retained regression: J01/J02 and their ACs.
I reread the charter, original development plan and active journeys, AGENTS, traceability, ADR-0007, product alignment checkpoint, design review, domain contracts and changed implementation. The change addresses the next missing research actions rather than substituting another isolated viewer or prediction feature.

P03 can select two explicitly distinct candidates, inspect and save antibody/antigen correspondence, compare source models with linked orientation/zoom, physically select mapped atoms and the reciprocal sequence position, inspect model-internal computed confidence with limits, and save a proposed variant hypothesis with exact source observation and a next experiment. Both synthetic candidates carry declared model-specific scores in the main path. The missing-confidence negative uses a separate database lacking those source scores. Actual restart and fresh-database export/reimport retain the records. A proposed hypothesis remains a proposal; no improved molecular function or measured result is asserted.

P04 can order observations within their exact recorded unit/assay/source context, follow a source-reported position to its actual sequence/structure, inspect computed notes separately from measured Material evidence and conditions, review/save a source-numbered child and lineage, and retain the proposed explanation, original Evidence IDs, limitations and next test. Original parent/Material records remain unchanged, and the child acquires no measured evidence, structure or verified numbering through inheritance. Restart and JSON roundtrip preserve the result.

Evidence position anchors are explicitly source-supplied associations through that Evidence's own subject path, not causal assignments of whole-Material scalar measurements to a residue. Descriptions stay raw source text. Annotation, computed and measured kinds retain their identity. Null qualitative observations receive no fabricated numeric score. Exact structural context preserves all source residue fields and alternate identifiers; source-only antigen/other selections do not manufacture antibody sequence correspondence or Material attribution. Unknown models, alternates, occupancy and B-fields remain unknown.

## Independently replayed evidence

All commands exited zero on the frozen source. Python 3.12.10, Gemmi 0.7.5, Chrome 156.0.8078.79, locally pinned 3Dmol 2.5.5. Temporary test databases and loopback servers were used; the user's research database was not accessed.

| Independently executed command | Result | Preserved evidence |
|---|---|---|
| `.venv/Scripts/python.exe -m pytest -q --tb=short` | 320 passed | `M3-observation-independent-python-run.log` |
| `node tests/j01-browser.cjs` | 5 checks PASS, including full J01 + both prescribed negatives | `M3-observation-independent-J01-results.json`, corresponding `j01-run.log` |
| `node tests/j02-browser.cjs` | 4 checks PASS, including full J02 + both prescribed negatives | `M3-observation-independent-J02-results.json`, corresponding `j02-run.log` |
| `node tests/observation-journeys-browser.cjs` | J03 three + J04 three + public-source scale one PASS | `M3-observation-independent-J03-results.json`, `M3-observation-independent-J04-results.json`, `M3-observation-independent-public-results.json`, `M3-observation-independent-journeys-run.log` |
| `node tests/observation-representation-independent-browser.cjs` | 4 independently proposed edge groups PASS | `M3-observation-independent-representation-results.json`, corresponding `representation-run.log` |

These are 20 browser checks personally rerun by this reviewer. I also inspected the implementation agent's frozen-source retained replay logs: foundation 11, numbering 5, structural 11, earlier observation races 3, design/hypothesis races 4 and save/draft races 3; all PASS, 37 additional checks. Logs are `M3-observation-final-retained-{browser,numbering-browser,structures-browser,observation-independent-browser,design-hypotheses-independent-browser,design-save-independent-browser}.log`. Combined evidence is 320 Python tests and 57 browser checks. Test totals do not replace the named journey outcomes or scientific/user gates.

The new full paths include actual physical canvas clicks, actual mouse camera motion, explicit source/map review and saving, hypothesis/design review before persistence, real process restarts, and exact export/reimport checks. The new suite blocks unexpected outbound browser requests and records no JavaScript errors. Existing hostile-input, CSRF/origin, identity and append-only tests remain retained.

## Independently proposed and exercised boundaries

`tests/test_observation_source_independent.py` adds eight tests. Typed exact keys cannot normalize float/bool model or residue numbers to integer coordinates, or unknown/null segment to blank. Wrong residue name/alternate reject. A genuine unknown source model and alternate are retained through hypothesis preview/save/restart without invented model one, occupancy or B-values. A measured whole-Material zero with a reported position remains measured zero on that Material; other legacy records retain absent optional fields exactly.

`tests/observation_review_fixture.py` and `tests/observation-representation-independent-browser.cjs` independently construct and exercise geometry boundaries:

1. Known common atoms retain native distance-based visual bonds, while A/B-incompatible alternate atoms, unknown alternate states and unknown elements receive no spurious bond. Stored source/coordinates/hash remain unchanged.
2. C-alpha overview includes actual carbon CA atoms in standard amino-acid residues, excluding a calcium ion named CA, a modified MSE residue, an unknown-element CA and a standard residue lacking CA. No pseudo-atom appears. A calcium ion deliberately placed directly in front of a visible protein CA cannot steal a physical pick while hidden. Selection detail shows the actual existing O atom for a missing-CA residue.
3. A physically selected source-only residue with an unknown alternate retains null and exact source identity in the reviewed proposal, with no antibody sequence reference. Focus → fit source → focus changes only framing and retains the selection. An unavailable sequence position clears the old source selection and disables focus; its later hypothesis cannot reuse an old source residue. Source text/keys/draft explanations do not enter localStorage. Source-note markup displays as literal text, and its reported-position action follows the exact map.
4. A held source response cannot reopen an obsolete hypothesis after the user navigates and changes the current candidate selection.

The fourth boundary initially reproduced a real stale-intent defect: after R reload, a delayed structural source resolution opened the old hypothesis modal over an Explorer selection changed to zero candidates. The implementation agent added a complete invocation-context guard alongside the existing project/epoch checks. The retained independent test now passes. The pre-fix reproduction is preserved as `M3-observation-before-intent-guard-independent-failure.json`; it is historical failure evidence, not the final result. No product source was edited by this reviewer.

I also identified a Windows checkout reproducibility gap for the raw public CIF: `core.autocrlf=true` could have changed pinned upstream bytes. The implementation agent added a `-text -whitespace` attribute for public CIFs and included `.gitattributes` in source inventory. `git check-attr` and the raw SHA were rechecked; the current file remains byte-identical to the pinned archive input.

## Reuse, source validity and real-scale interpretation

The documented pre-interface benchmark compares established [Mol* component/display patterns](https://molstar.org/viewer-docs/managing-the-display/) and [3Dmol native model operations](https://3dmol.org/doc/GLModel.html), with Jalview source-position links already recorded in SCIENTIFIC_UX.md. I rechecked the primary documentation and the installed behavior. Existing rendering/focus primitives are reused. The custom work enforces the workspace's subject/source/reasoning identities; it does not introduce another renderer, prediction algorithm or secondary-structure engine.

Native bond assignment is a coordinate-distance rendering aid, not a chemical-connectivity or valence claim. C-alpha mode is explicitly an atom subset, not a cartoon or inferred secondary structure. Exact source fields remain inspectable. Unknown and unmapped cases are visible, and model-internal scores are never presented as measured affinity or synthesized from B-values. English implementation/UI and the English/Japanese guide preserve scientific meaning; retained bilingual checks pass.

The pinned experimental [PDB 1MLC entry](https://www.rcsb.org/structure/1MLC) has raw SHA-256 `5536c79a3d73e09503f6a4d252bbca2dac5fa0e59b5424309f49cd0c34e8606e`. Source revision/retrieval/authors and [PDB archive data usage](https://www.rcsb.org/pages/policies) are recorded in `fixtures/public/README.md` and third-party notices. The input is a public experimental coordinate file, not a model prediction, and no runtime download is used.

The checked file retains 8792 atoms and 1332 source residues, including 1122 polymer residues and 210 waters; six protein chain instances and separate water label-asym IDs remain distinct. Primary Fab A/B is explicitly mapped from deposited sequences/label positions; the second Fab copy, lysozyme targets and water are preserved as separate source instances. No sequence-equality collapse or automatic biological-assembly transformation occurs. The reviewer inspected the actual rendered focused-source screenshot as well as the source/representation checks. The real-scale check establishes local rendering and source preservation, not predictor accuracy, human scientific goldens or real researcher usefulness.

## Gates, limitations and integration boundary

Identity, provenance, local-only confidentiality, retained regression and independent workflow gates: **PASS within this reviewed scope**. No unresolved P0/P1 defect was identified in the reviewed implementation. This is not a zero-defect assertion for the whole product or an ASVS/performance/scientific-validation claim.

Once exact-source reports and the eventual actual implementation commit are bound by the separate registration check, current synthetic engineering acceptance can be recorded as J01–J04 **4/8** and their prescribed negatives **8/16**. Unimplemented/unverified J05–J08 must not be counted. J05 interactive composition, M4 construct/material comparison and finalized decisions, full J08 adapters, performance/coverage/security release gates, human scientific reference checks and all eight actual researcher evaluations remain open. Full M3 and the complete product goal remain unfinished.

The next research-value priority is the missing composition/construct/decision workflows, not additional isolated representation controls, prediction engines or cosmetic expansion. The narrowed reuse approach serves P03/P04's continuous research action while keeping source uncertainty and researcher judgment explicit.
