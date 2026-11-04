# F19/F20 / J07 final engineering integration review

Verdict: **PASS for frozen-source J07 integration with retained J01-J06.** The evidence supports **7/8 main journeys and 14/16 prescribed negative flows**, and the **M4 engineering gate for J06/J07**. Actual implementation-commit binding and acceptance registration are the next separate step. Full J08, scientific golden validation, actual researcher evaluation and final release quality remain unfinished; this is **not Release 1.0 or whole-product completion**.

Reviewer: `/root/j06_design_review`, separate from implementation. Date: 2026-11-04, Asia/Tokyo. Trace: F19 / P07 / J07 / AC-J07 for explicit criteria/missingness; F20 / P07/P08 / J07/J08 / AC-J07/AC-J08 for fixed decisions, revisions and reproducibility, with retained P01-P06 / J01-J06 / their ACs. This reviewer personally executed the full Python suite and all twelve browser scripts below on the final frozen source. Product/test source and active acceptance metadata were not edited during final integration.

## Exact source and evidence ownership

Final source identity: **`48b183a7c1bb088a86ef94b6777473f530c2aae21d01c55ef0e1a9d5e562921b`**, **91 files**. The implementation manifest is `M4-decisions-freeze-source-manifest.json`; this reviewer independently generated `M4-decisions-independent-source-manifest.json`. Their complete inventories/digests match. Every actual working source file was checked before testing, after each browser script and again after evidence restoration. No source mismatch or runtime/test change occurred.

The source was an uncommitted implementation on metadata baseline `76a9f29e8adec4695d244dceaca58e0180936a8d`; the previous registered product-source baseline was `2c2a96ffe67dc58ab8110b72c839a3948288a914`. This report identifies the tested working tree by its exact manifest rather than assigning results to a future commit. The named J07 negative2 uses the strengthened raw Python fixture and actual context check, not a JavaScript-cloned later observation with changed numeric condition types.

Execution ownership is explicit:

| Verification | Executed by | Result and evidence |
|---|---|---|
| Full Python suite | **This reviewer**, independently of implementation | **452 passed in 48.78s**, exit0; `M4-decisions-independent-python.log` |
| Separate full Python suite | Implementation agent; log inspected here | **452 passed in 39.23s**; `M4-decisions-final-python.log` |
| Six retained foundation/numbering/structures/ownership browser scripts | Implementation agent on the same freeze; actual logs inspected here | **37 checks PASS**, all exit0; `M4-decisions-final-retained-*.log` |
| Named J01-J07 and remaining affected browser scripts | **This reviewer**, fresh personal executions on the final freeze | **All twelve scripts exit0/PASS**, as listed below |

The 37 retained checks are 11 foundation, 5 numbering, 11 structures, 3 observation-request ownership, 4 hypothesis ownership and 3 pending-save ownership checks. I inspected their actual results/behaviors as well as both full Python logs. Browser runs were sequential and started after the implementation agent's browser batch ended; this avoids a possible execution confound and is not a diagnosis of an earlier startup incident.

## Final personal browser replay

Each command is `node tests/<script>`, using the repository Python environment, installed Chrome/Playwright, the existing runtime `NODE_PATH` documented in the bounded review, isolated temporary databases/loopback servers and labelled synthetic fixtures. No dependency installation, proprietary-data input or research-database mutation was needed.

| Script | Confirmed result | Independent result suffix under `TEST_EVIDENCE/M4-decisions-independent-` |
|---|---|---|
| `j01-browser.cjs` | 5 PASS: full J01, two prescribed negatives and language/privacy checks | `J01-results.json` |
| `j02-browser.cjs` | 4 PASS: full J02, two prescribed negatives and privacy check | `J02-results.json` |
| `observation-journeys-browser.cjs` | J03 3, J04 3, separate public source-scale 1 PASS | `J03-results.json`, `J04-results.json`, `public-results.json` |
| `j05-browser.cjs` | 4 PASS: full J05, both prescribed negatives and privacy check | `J05-results.json` |
| `j06-browser.cjs` | 4 PASS: full J06, both prescribed negatives and fresh typed roundtrip | `J06-results.json` |
| `j07-browser.cjs` | 4 PASS: full J07, both prescribed negatives and fresh typed roundtrip | `J07-results.json` |
| `observation-representation-independent-browser.cjs` | 4 geometry/source-identity groups PASS | `representation-results.json` |
| `composition-independent-browser.cjs` | 6 endpoint/ownership groups PASS | `composition-results.json` |
| `experiments-independent-browser.cjs` | 8 Construct/Material/import ownership groups PASS | `experiments-results.json` |
| `decisions-independent-browser.cjs` | 6 independently added decision source/ownership/version groups PASS | `decision-edges-results.json` |
| `numeric-transport-browser.cjs` | Actual typed import/export/reimport pipeline PASS | `numeric-results.json` |
| `numeric-transport-guards-browser.cjs` | 4 raw-snapshot/direct-import/Unicode groups PASS | `numeric-guards-results.json` |

`M4-decisions-independent-replay-summary.json` records all twelve commands, exit codes, durations and result artifacts; each has a matching independently captured run log. Fresh screenshots of source-numbered design, structural/property reasoning, composition, Construct/Material observations, J07 review and frozen draft have the same prefix. The named result files contain the seven required main test names and all fourteen prescribed negative test names. The public experimental 1MLC test is source/scale observation only, not another journey, prediction validation or a human scientific golden.

## Coherent J07 action and mandatory gates

The researcher selects three actual comparison candidates in E, declares three original binding/property/expression contexts in R, explicitly enters importance/preferences and chooses actual observations. No sole record is silently selected; alternative lots remain separate. Observed zero, selected null scalar and unchosen observation remain distinct. The researcher retains a proposed Hypothesis and its original-source closure, saves draft1, changes declared binding importance, inspects an original source in W, returns without losing candidate IDs/reason/weight, and saves finalized2 with visible predecessor changes and a chosen subset.

Required missing expression prevents finalization even when the missing candidate is unchosen and the criterion weight is0. The researcher may save draft3, then explicitly change the requirement/reason and save finalized4; missing optional data remains visible. Later Evidence is imported through actual controls using original raw Python JSON so condition25.0 stays a float. The real decision-context API confirms exactly three cohorts and both old/new binding IDs in the same context. That new same-context observation does not alter finalized2 or its frozen original value. Actual server restart, native download and file reimport into a second SQLite database preserve all four versions, chosen IDs, sources, hypotheses, timestamps and typed snapshots, verified with canonical Python JSON.

- **Identity: PASS.** Actual Molecule/Construct/Material/lot/Evidence/Decision identities remain distinct through source inspection, criterion choices, continuation and transfer. Equal labels/sequences/units do not establish identity. Legacy shortlists preserve their exact old shape and remain drafts; continuing one creates a separately identified new-contract revision.
- **Provenance: PASS.** Criteria anchor actual eligible contexts; original measured/computed kinds, units, typed conditions and source/version remain separate. Chosen records and supporting proposed hypotheses retain their actual subjects/status and frozen source closure. Declared importance/preferences are not normalized, converted into scores or interpreted as biological confidence. Finalized means fixed record, not validated conclusion or authenticated authorship.
- **Security: PASS for the tested local scope.** The shared strict server validation, local session/Origin/CSRF, atomic import and no-external-transmission default remain. Browser suites that record outbound traffic and JavaScript errors report none. New private decision notes/source content/choice payloads stay out of localStorage. Synthetic competing-client requests use the real authenticated local review/import APIs and authoritative serialized bundles, not an application callback or validation bypass.
- **Regression: PASS for this frozen engineering scope.** Full452 tests exercise the shared Decision/graph validators as well as retained modules. Personal J01-J07 main/negative paths and the retained37 checks pass. Source-coordinate/unknown-confidence behavior, unlike units/unknown conditions, no parent measurement inheritance, original observations, legacy drafts, raw numeric transport and immutable snapshots remain established. No unresolved P0/P1 defect was identified in this reviewed scope; this is not a claim that all future data, deployments or release gates are defect-free.

The separate fresh design/domain review and bounded UI review remain relevant evidence: `M4-decisions-design-independent-review.md`, `M4-decisions-domain-independent-review.md` (40 domain/API cases including eight independent boundaries) and `M4-decisions-ui-independent-review.md` (four main groups plus six added browser groups). The domain cases are also included in the final full452 replay. All six added UI edges were personally rerun: delayed context preserves input; incompatible contexts do not enter choices; edited/project/selection previews remain owned; old rejection cannot unlock a newer save; old success cannot erase another project; and a genuinely advanced predecessor rejects a stale UI save without creating a fork. Old records and frozen drafts stay correctly labelled and read-only when inspected.

## Evidence preservation and recorded incidents

Every new generic result/image was copied immediately after its successful run, before historical restoration. The implementation agent then restored31 tracked runtime outputs to their literal existing HEAD blobs and two uncommitted bounded-UI outputs to this reviewer's exact pre-final backups. I independently checked all31 restored hashes/current-run-copy hashes, both backups, the bounded manifest's15 source/document hashes and seven evidence hashes, and all91 frozen source hashes after restoration. See `M4-decisions-historical-byte-preservation.json` and `M4-decisions-pre-final-bounded-preservation.json`. Old evidence was not replaced with new results or silently reclassified.

The bounded UI report is unchanged at SHA-256 **`7f0d496b70e2b9e7c41be4d7c3c2ce3aca5d55915c15cb9f424bef59b1f25093`**. Its benchmark document was restored to the reviewed bytes; future J08 preparation is separate, outside this approval. Raw final artifact hashes, captured after restoration, are in `M4-decisions-final-independent-evidence-sha256.json`.

The earlier J06-stage startup timeout remains a preserved, unreproduced incident with unknown cause. The current observation script retains its failure diagnostics; this final J03/J04/public execution passed, and no recurrence was observed. No cause or product correction is invented from those successful retries. The bounded Playwright gate-fixture failure and the earlier strengthened same-context test correction are transparently recorded in the bounded review; neither is a concealed product defect. No new runtime failure occurred in this final replay and no product fix was needed.

## Scientific usefulness and remaining product work

P07 can now inspect original observations and gaps, declare criteria/importance, retain trade-offs and the actual choice, and later explain a distinct revision without changing old reasoning. This completes a continuous research action rather than merely adding a weight editor. P06's actual Construct/Material/source comparisons remain usable; P08 gains fixed decision dependencies through exact project transfer. Native source tables, progressive provenance disclosure, explicit choices and existing append-only records implement the documented JMP/Galaxy interaction patterns without an optimizer, arbitrary score, new runtime or new primary screen. The independently captured J07 screenshots and earlier bounded visual inspection support that assessment; actual researcher evaluation remains required for practical acceptance.

The largest remaining engineering gap is **full J08**: complete supported-format/adaptor coverage and the end-to-end reproduction/reuse action. The tested awx/1 transfers do not substitute for all required J08 inputs. Scientific goldens, evaluation by the actual eight researcher roles, specified coverage/performance/storage/security measurements and final 8/8+16/16 release integration remain open. Stage metrics support this decision but do not establish biological validity or usefulness by themselves. This PASS supports the M4 J06/J07 engineering gate and subsequent seven-journey registration; it does not alter the original eight-persona goal or authorize product completion.
