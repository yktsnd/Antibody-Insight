# F07 imported numbering: independent implementation review

F07 implementation: **PASS**.
Full M2 milestone, complete J01/J02/J08 and Release 1.0: **NEEDS-EVIDENCE**.

Reviewer: `/root/independent_review`, separate from the implementation agent.
Date: 2026-11-03, Asia/Tokyo.
Baseline: `1a0258754fddce41f517d5c561bfcc557578d9ef` plus the reviewed F07 working-tree changes.
Exact reviewed source set: TEST_EVIDENCE/M2-F07-independent-source-manifest.json, digest `5e0ed23d037ceecaf0d3ab59c3add83853f29ba72ef728af9ca60fb1c6069b8e`.

## Scope and method

P01/P02/P08 → J01/J02/J08 → AC-J01/AC-J02/AC-J08, F07 import/observation only.
The reviewer inspected workspace_app/numbering.py, domain/adapters/fixtures/server changes, the UI map/group/state changes, both browser suites and the numbering tests against approved ADR-0003, NUMBERING_CONTRACT and the primary-source design review.
The reviewer added tests/test_numbering_independent.py and evidence files, without changing product code.

The implemented action is E import/preview/save → W inspect exact named chain/domain/raw-index/IMGT coordinate/region/source → E explicitly resolve ambiguous heavy-domain maps and group complete CDR3 → retain candidate/map/chain selections after restart. This imports externally supplied declarations; it does not execute numbering, align structures, create numbered variants or validate antibody biology.

## Independent execution and evidence

- `python -m pytest -q`: **159 passed in 15.97s**, exit 0, including 33 independently added numbering cases and all retained tests.
- `node tests/numbering-browser.cjs`: **5 checks PASS**, exit 0, Chrome `156.0.8078.79`. The final report is TEST_EVIDENCE/M2-numbering-browser-results.json at `2026-11-02T15:14:58.774Z` (2026-11-03 JST). It independently verifies 800 imported candidates, five retained selections, exact insertion identities and H/L distinction, unavailable/unverified/partial/ambiguous states, rejected malformed choices, actual server restart, source preservation, no outbound requests and no JavaScript errors.
- `node tests/browser.cjs`: all **11 retained assertions PASS**, including no-outbound/no-JavaScript-error assertions. The process then exited **1** because opening the existing M1-browser-results.json for writing raised a Windows/OneDrive `UNKNOWN` filesystem error. This was not an application assertion failure. All 11 observed results and the original exit/error were verified and preserved in the uniquely named TEST_EVIDENCE/M2-retained-foundation-browser-review.json. The product was not changed to conceal or bypass the error, and the command is not reported as exit 0.
- `python scripts/check_traceability.py`: **PASS** for eight journey definitions/seven implementation slices; complete final journey acceptance remains **0/8** and prescribed final browser negatives **0/16**.
- TEST_EVIDENCE/M2-numbering-screen.png and M2-numbering-explorer.png were visually inspected. Raw/IMGT coordinates, domain/map identity, explicit synthetic/attestation labels, CDR3 groups, selected IDs and the ambiguous-map selector are readable. Screenshots supplement stored-data assertions rather than establish scientific correctness.

The full Python run preceded the final English/Japanese help and D scope wording adjustment; those wording-only changes were separately inspected and are included in the final reviewed source manifest. Browser replays exercised the final UI. Observed commands/results are retained in M2-numbering-independent-test-log.txt.

## Acceptance replay

| F07 requirement | Result | Independent evidence |
|---|---|---|
| Exact imported identity | PASS | Named Molecule/chain/domain/map identities retained; same coordinates on H/L remain distinct; a same-sequence second molecule acquires no implicit map; actual cross-project same-sequence reference rejects atomically |
| Supported IMGT definition | PASS | Rearranged V-domain only; 13 independently asserted region boundaries follow the named nomenclature source; 111/112 extensions are strings with integer suffix ordering, including `.1` versus `.10` |
| Source and failure states | PASS | Source/version and attestation metadata persist; failed/unavailable records cannot carry successful coordinates; unverified maps remain inspectable but do not group; synthetic fixtures require explicit project metadata |
| Complete CDR3 only | PASS | Anchors 104/118 and nonempty observed CDR3 required; truncated or anchor-only maps never become full/empty groups; valid short-loop gaps remain gaps without fabricated residues |
| Explicit ambiguity handling | PASS | Two actual heavy domains on one chain and alternate map versions require exact map choice; wrong/unverified/non-heavy/unknown choices reject; choice survives restart |
| State and privacy | PASS | Candidate/chain/raw-index/map choices preserved; grouping persists opaque map IDs rather than CDR3 sequence; browser assertion verifies the displayed CDR3 is absent from localStorage |
| Persistence/regression | PASS | Immutable stored map JSON survives restart and empty-DB roundtrip in unit tests; old optional-field absence stays absent; all prior tests and browser product assertions pass |

## Independent cases and corrections

The 33 cases comprise long insertion sequence-order/persistence, 13 authoritative boundary cases, five supported-subset/noncanonical-coordinate negatives, two partial/empty-CDR3 cases, a valid short gapped CDR3, two heavy domains in one chain, four falsy-choice negatives, unknown choice keys, equal-sequence distinct identity, actual cross-project identity, old project classification absence, and two unknown nested-field cases.

Three issues were identified during review and corrected before this verdict:

1. **Malformed map choice silently ignored.** `choices or {}` accepted false/zero/empty-string/list values as the default and ignored unknown molecule keys. The function now distinguishes an omitted argument using a sentinel and validates the supplied object, known molecule keys and nonempty map-ID values. Independent tests and the actual HTTP browser cases reject the malformed inputs.
2. **CDR3 copied to browser persistence.** The first UI version stored the selected group sequence in state.cdr3Filter, which remember() persisted to localStorage contrary to DATA_CONTRACT. Groups now expose opaque representative map IDs; state.cdr3Group stores only an ID. A known-state whitelist drops the old field, and the browser checks that the displayed CDR3 sequence is absent from localStorage.
3. **Reload/navigation readiness race.** Navigation could run before asynchronous project/numbering restoration finished and then be overwritten by the restored screen. Initial and project-load navigation/project/import controls now remain natively disabled until data are ready. The actual browser scenario, without replacing the assertion with a scientific bypass, succeeds after correction.

No unresolved P0/P1 defect was found in the reviewed F07 scope. The artifact-write error is preserved as an execution-environment limitation, with its complete assertion evidence saved separately.

## Scientific and compatibility boundary

The scientific definition was checked in TEST_EVIDENCE/M2-numbering-design-review.md against [IMGT FR/CDR definitions](https://www.imgt.org/IMGTScientificChart/Nomenclature/IMGT-FRCDRdefinition.html), [V-DOMAIN insertion tables](https://www.imgt.org/IMGTScientificChart/Numbering/IMGTIGVLsuperfamily.html), and [additional positions](https://www.imgt.org/IMGTScientificChart/Numbering/IMGTnumberingAC.html). The implementation uses the explicitly chosen FR4 endpoint 129 and records the differing 128 prose in another IMGT page. Legitimate 60.1/84A additions are rejected as unsupported by this subset, not declared scientifically impossible.

Source verification is an imported attestation with reference/reviewer/time, not proof established by the application. All current numbering fixtures remain synthetic engineering data; this PASS does not make them human-validated scientific golden fixtures. Unknown or unverified science is not converted into successful verified numbering. External service calls, biological predictions and artificial confidence values are absent.

Project.data_class is optional with absence interpreted as research without rewriting old records. Old molecules, component graphs, Material ownership, Evidence kinds and immutable drafts retain their meanings. Existing loopback/session/Origin/CSRF/CSP/transaction controls remain in use, and both browser replays observed no outbound requests. This is not an ASVS certification or complete endpoint/OS security audit.

## Remaining gates

Full M2 still requires structure import/view/correspondence and its negative mapping cases. Full J01 still needs assay-aware sorting and the complete specified selection/evidence path; J02 requires numbered child design and saved reasons; J08 requires the remaining adapters and final cross-format/structure/decision roundtrip. The other journeys, 18 human-validated scientific golden fixtures, researcher evaluation, final branch coverage/performance/storage/security gates and complete independent eight-journey replay remain pending.

F07 may integrate with its exact reviewed revision and evidence recorded. No full M2 or Release 1.0 completion claim follows from this review.
