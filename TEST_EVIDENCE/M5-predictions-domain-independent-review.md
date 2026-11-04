# M5 prediction import: independent domain/API implementation review

Verdict: **PASS for the reviewed F21/F22 domain/API implementation only.** No domain/API defect was found in this bounded review. Browser interaction, complete J08, retained seven-journey replay on the final integrated source and release acceptance remain pending. This report does not advance TRACEABILITY or the last verified baseline of seven main flows and fourteen prescribed negatives.

Reviewer: `/root/prediction_design_review`, separate from implementation. Date: 2026-11-04, Asia/Tokyo. Trace: F21 / P03,P08 / J03,J08 / AC-J03,AC-J08 and F22 / P08 / J08 / AC-J08. Source was an uncommitted implementation on HEAD `14c365c3e12221c4fbb941131253676ed0ff0845`, application `0.7.0-dev`. The registered J01-J07 product source remains `b7eabac029024546a25429abfeb262e1a0ba2662`. Only tests and new evidence were written by this reviewer; product code, ADR, baseline acceptance and historical reports were not edited.

## Scope, identity and evidence

Replayed the approved design against PRODUCT_GOAL, original P03/P08, J03/J08 and their AC/negatives in DEVELOPMENT_PLAN, AGENTS, TRACEABILITY, product alignment, ADR-0011 and the independent design review/addendum. Inspected predictions.py plus domain, adapter parser, structure metric validation, transactional storage, authenticated server routes and existing exact-bundle browser transport. The latter inspection is design context, not a browser result.

The source/test/contract inventory is `M5-predictions-domain-independent-source-manifest.json`: fifteen files, SHA-256 hashes and byte counts, interpreter and HEAD. `M5-predictions-domain-independent-source-stability.json` independently recomputes every hash after the final replay: **15/15 match**. The exact reviewed core hashes are:

| File | SHA-256 |
|---|---|
| workspace_app/predictions.py | `6eb0d8c8e97d28b0c19e9298f857148c767c5ca01054af4e5522e4ffee712716` |
| workspace_app/domain.py | `ae624e70cc04edcdcf05cdc12a32d9c4d3c3fe5111056076996aa50a298c7df6` |
| workspace_app/structures.py | `864e93f87fb610f75ef6679c1c4f42c7a3208e6636aa18c3c67de274373681e9` |
| workspace_app/storage.py | `baf15ff5ad928e19ee6a7157ef1a82683bb5102ee517596aece1e5219841e116` |
| workspace_app/server.py | `aa634dba9b719b99852c0ee5346801b9a11c4d6abfee8797823910f6c1504c24` |
| tests/test_predictions_independent.py | `8b01b2853a1ba852cae59a4d004db2f0e6711c95fc21903e33107b88c715daff` |

The final authoritative command was:

```powershell
& ./.venv/Scripts/python.exe -m pytest tests/test_foundation.py tests/test_structures.py tests/test_structures_independent.py tests/test_predictions.py tests/test_predictions_independent.py -q --tb=short
```

Result: **159 passed in16.01s**, captured in `M5-predictions-domain-independent-targeted-replay.log`. This includes the implementation's51 prediction cases and **17 new independent domain/API cases**. Runtime: Python3.12.10, Gemmi0.7.5, pytest8.4.2. The earlier prediction-only replay logged68 passes; the final run includes strengthened direct-ID and pre-tamper assertions and is the acceptance evidence for the exact final test hash.

One initial invocation used global Python instead of the existing .venv and produced32 fixture failures because Gemmi was absent, with19 passes. No product change was made in response. Selecting the existing pinned application environment resolved that setup error. No repeated speculative repair or hidden failing product case is claimed.

## Independent replay and added edges

1. **Eight distinct exact subjects despite equal labels/sequences.** Constructed two Molecule branches with identical chains, names and lot labels; each has its own Construct, Material and computed Structure. Tested all four roles on both branches through direct typed IDs and explicit opaque mappings. The eight Evidence subjects stay distinct. Tokens include `/`, `~`, Unicode, surrounding spaces, `__proto__`, `constructor` and HTML-like text. Raw BOM/CRLF JSON, bindings and exact records survive SQLite save, reload and reversed-entity fresh-store replay. This is domain safety; browser rendering of these tokens remains to be tested separately.
2. **Two structures both have model1.** Validated two simultaneously imported, otherwise identical native files linked to different actual structures. Separately changed only Evidence subject, source target, source model or source conditions. All four forged associations reject atomically and leave the original project unchanged. A common model number or visible name does not merge their identities.
3. **Complete schema-path scan.** Placed unknown fields in separate records, a source object and multiple residue-reference objects, with `/` and `~` in field names and an unrelated unresolved subject. The full correctly escaped pointer list appears before rejection. Arbitrary nested typed conditions remain opaque data and are retained, rather than being mistaken for schema fields.
4. **Allocation and origin constraints through direct awx storage.** Removed a reverse allocation while retaining its Evidence, added an unallocated second Evidence, changed computed kind to annotation, changed source project and mixed an unrelated measured import_origin into a source-backed computed record. All reject without writes. The implementation's cases additionally test identical-row pointer swaps, source hash/content changes, typed values/conditions, missing source/Evidence and duplicate allocation.
5. **Reserved malformed tokens cannot become aliases.** Tested malformed molecule, construct, prediction-file and Evidence prefixes, plus a control character. Explicit mapping cannot redirect any into an actual subject. The implementation's tests also cover well-formed unavailable/wrong-type IDs, stale digest, unused mapping and foreign target.
6. **Actual local HTTP boundaries.** Used a real server on an ephemeral loopback port and its session cookie/CSRF flow. Invalid UTF-8, wrong Origin, wrong CSRF, absent session, unsupported content type and Content-Length over32MiB reject with422/403/415 as appropriate, without changing stored data. A following valid preview succeeds with a distinct one-source/one-value count and still performs no writes.

These cases are synthetic engineering fixtures, explicitly labelled as having no real model execution or scientific meaning. No actual private sequence or experiment was transmitted to an external service.

## Scientific meaning, compatibility and mandatory gates

The new prediction_file is a narrow immutable raw-source record, not a protein/construct/material identifier. Existing generic append-only SQLite storage and complete awx transport are reused. F16 row metadata and coordinate-specific Structure content have not been repurposed. Allocations are reciprocal importer associations; they are not a causal provenance DAG, evidence of scientific independence or authentication of an external run. A self-consistent new external package can only provide recorded attestation. Existing stored IDs/records cannot be updated silently.

The [official AlphaFold3 output definition](https://github.com/google-deepmind/alphafold3/blob/main/docs/output.md), independently checked in the design review on the same date, defines the four selected scalar ranges and separate array scopes. Code preserves those names/scopes, requires an actual computed Structure/model and source event time, accepts explicit unknown version, and rejects malformed recognized scalars for the entire native summary. It does not calculate ranking, affinity, missing scores, atom/residue confidence or external sample identity. Unmapped booleans/arrays remain original text plus listed paths. Canonical measured/literature/annotation rows are excluded rather than relabelled computed. Missing scalar/null/zero stay distinct; typed origin comparison detects int/float and signed-zero changes.

| Mandatory gate | Bounded result and evidence |
|---|---|
| Identity | **PASS:** all four direct subject roles, explicit mapping, same-model1 separation, reserved/foreign/stale refs, allocation uniqueness and fresh-store exact replay |
| Provenance/scientific meaning | **PASS:** raw UTF-8/BOM/CRLF/hash preservation, typed source-backed scalar/context consistency, explicit source time/version, model scope and atomic forged-reference rejection |
| Security | **PASS for reviewed local domain/API scope:** actual session/Origin/CSRF/UTF-8/body/type checks, strict schemas and unchanged data after rejection. Browser XSS, localStorage and outbound-traffic monitoring remain separate pending checks |
| Regression | **PASS for targeted foundation/structure compatibility:**159 selected tests pass, including unchanged-record and rollback behavior. No all-journey or final integration result is inferred |

The complete-project UTF-8 JSON-escaped wrapper is checked in prediction preview and both storage append paths. The targeted tests exercise an actual sub24MiB raw source whose escaped representation exceeds the32MiB transport envelope, exact wrapper boundaries, legacy shortlist append and prior oversized-record readability. The app rejects before persistence, rather than truncating or splitting. Existing over-limit projects remain readable/exportable; their replay under the limit is not claimed. Earlier FASTA/CSV provenance remains its actual recorded data/digest scope, without claiming absent raw originals.

## Product alignment and remaining acceptance

This implementation lets P03/P08 register actual supplied computed scalars with inspectable original source and exact subjects, then reconstruct them without silently changing scientific meaning. Reusing reviewed import, immutable entities and existing project transport keeps the approach proportional. A generic array interpreter, workflow engine or prediction service would add effort and unsupported assumptions without closing the required research action.

The largest remaining gap is still the full original J08 action in the browser: actual FASTA, structure, measured CSV and both supported prediction controls; sequence/coordinate/source correspondence in W; kinds/source/version/time/Material in R; saved Hypothesis/Lineage/fixed Decision revisions; native export, actual restart and fresh-store file reimport with exact IDs/kinds/mappings/raw retained content and history. J08 duplicate-ID and corrupt-structure negatives must be replayed there, with all retained J01-J07 and fourteen negatives on the frozen integrated source. Preview/save ownership, source drill-down, safe raw display, browser typed transport and confidentiality need independent browser evidence.

This domain/API PASS supports further implementation within the approved design. **It does not mark J08, M5 or the product complete.** Human scientific goldens, actual eight-role researcher evaluation and final coverage/performance/storage/security/release requirements remain open.
