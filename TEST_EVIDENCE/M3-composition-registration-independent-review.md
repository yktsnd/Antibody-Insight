# F14/F15 acceptance registration: independent verification

Verdict: **PASS for current J01–J05 engineering registration and the reviewed documentation.**
Reviewer: `/root/observation_review`. Date: 2026-11-04, Asia/Tokyo.
J06–J08, scientific golden validation, actual researcher evaluation and Release 1.0 remain **NEEDS-EVIDENCE**.

This verifies the pending registration/docs against actual implementation commit `d4bafb8830b10a08f47b346f0a6f13af315425e7`. Only this separate report was authored by the reviewer in this step. No runtime, test, script, data, active acceptance metadata or hashed implementation review was edited; no broad test suite was rerun.

## Source and literal artifact identity

All73 source-inventory entries match the exact independently tested working-tree digests. The inventory itself matches the current source-file set, and its aggregate digest recomputes to `41a4e108d90a0e35dd0ff1dfcbfc1456b1890a4bc8d723c9c178aed219950623`. No source changed after freeze. Every file exists in the actual implementation commit. Ordinary committed text matches under Git CRLF/LF normalization where applicable; this does not claim universally identical source-text line endings across platforms.

New milestone evidence was protected by `TEST_EVIDENCE/M3-composition-* -text -whitespace` before freeze. I directly retrieved each registered review/test/manifest through `git show <actual-commit>:<path>` and verified the literal raw SHA-256 against registration metadata. No normalized-JSON substitute was needed:

| Artifact | Verified raw SHA-256 |
|---|---|
| Main independent implementation review | `bbd45a928b587fa8054d0ad554f9ed46bcfa7d6760cb4c96334c57d824d64ea0` |
| J01 named results | `508dd4309b2ab800bcb4de62d5abdf56ab7454a8bc67a0f62ac6a4ec59919100` |
| J02 named results | `56269ce8b4958487a5ca0b629b13612e17cce3e098ab12e6ad87b5428f4f1725` |
| J03 named results | `f6131284afd47f73bdff8a983a5b6173bcce1262bb01d49a84c03b44a02fb4d6` |
| J04 named results | `3ea3d6296973caa771661a214b579caccdf99063f797e0d29089716a83ac6968` |
| J05 named results | `2c64292843d6421645df07690a9ab0076f1798199c1ae880a6a77640cc4614e2` |
| Independent source manifest | `cb64a202afbad0d879dbbfd0026b82d2a2d7936f149e57cc85e281f7db8f55b8` |

## Acceptance and preserved history

TRACEABILITY and JOURNEY_ACCEPTANCE agree on persona/scenario/AC, reviewer `/root/observation_review`, PASS status, actual implementation commit and fresh M3-composition reports. Every registered main and both prescribed negatives occur uniquely with PASS in its named report:

- J01: `e2e_j01_candidate_shortlist`; `e2e_j01_invalid_sequence`; `e2e_j01_missing_measurement`.
- J02: `e2e_j02_humanize_variant`; `e2e_j02_numbering_unavailable`; `e2e_j02_insertion_mapping`.
- J03: `e2e_j03_complex_comparison`; `e2e_j03_unmappable_residue`; `e2e_j03_missing_confidence`.
- J04: `e2e_j04_developability_review`; `e2e_j04_unit_mismatch`; `e2e_j04_unknown_assay_condition`.
- J05: `e2e_j05_bispecific_composition`; `e2e_j05_undefined_chain`; `e2e_j05_unsupported_analysis`.

J06–J08 remain PARTIAL without fabricated acceptance entries or implementation commits. F14/F15 map to P05/J05/AC-J05, real implementation files, checks and the independent implementation review. `scripts/check_traceability.py` passes: **8 defined journeys, 15 traced slices, 5/8 accepted engineering journeys and10/16 prescribed negatives**. The source/artifact/commit checks above were also performed independently of that checker.

Comparing committed Git trees against prior registration commit `879aad700a4245a6118d4803f275034d52ca2ffe` confirms **120 earlier TEST_EVIDENCE artifact blobs unchanged**, excluding the intentionally updated human evidence index and active JOURNEY_ACCEPTANCE metadata. Historical M2/M3-numbered/M3-observation reviews, source manifests, named results and screenshots remain preserved. Fresh retained output uses the M3-composition prefix. Pinned 3Dmol asset/licenses, Gemmi license and public1MLC coordinates also match exact committed bytes.

## Scope and language consistency

README English/Japanese, PROGRESS, PRODUCT_ALIGNMENT English/Japanese, KNOWN_LIMITATIONS, CHANGELOG, COMPONENT_CONTRACT, ADR-0008 and the evidence index consistently describe version0.5.0-dev, current synthetic J01–J05 acceptance and M3's engineering gate. They preserve J06–J08, human scientific goldens, eight-role researcher evaluation and final quality gates as open. Historical stage counts are identified as historical rather than current. Japanese explanations retain the curated terminology policy and distinguish declared composition from demonstrated assembly, functional units, valency and chemistry; L11 remains explicit.

The documentation accurately retains352 Python tests and67 browser checks as the frozen implementation evidence. This registration check does not recast those tests as new executions, biological validation or actual researcher evaluation. No unresolved registration issue remains in the reviewed state. The next priority remains J06 construct/material measurement comparison, J07 finalized decision criteria/revisions and complete J08 reproducibility, under the original scientific and confidentiality principles.
