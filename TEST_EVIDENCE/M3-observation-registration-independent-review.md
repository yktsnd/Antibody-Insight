# F12/F13 acceptance registration: independent verification

Verdict: **PASS for current J01–J04 engineering registration and the reviewed documentation.**
Reviewer: `/root/observation_review`. Date: 2026-11-03, Asia/Tokyo.
Full M3, J05–J08, scientific golden validation, actual researcher evaluation and Release 1.0 remain **NEEDS-EVIDENCE**.

This is a separate read-only verification of source/evidence registration and documentation after the implementation review. The only file authored by the reviewer in this step is this report. No runtime, test, script, data, acceptance metadata or hashed implementation report was edited by the reviewer, and no broad suite was rerun for Git attributes/documentation.

## Actual source and reviewed-source equivalence

Runtime implementation commit: `8f11e87a17883656c0e859ae959fee228fdcb170`.
Final source/evidence archival commit used by current TRACEABILITY and JOURNEY_ACCEPTANCE: `983342a280b3580a9d8eaaa449034f96f150203c`.

The independent implementation replay tested frozen source digest `36f338e4ab813ebfcf12b2ca680e24cd993eb8c042a1a6e6cc1ea1db97d335c3`: 320 Python tests and combined 57 browser checks, with 20 browser checks personally rerun by this reviewer and the remaining 37 retained regression logs inspected. Those results are preserved in the unchanged implementation review and named reports; they are not represented as newly rerun tests in this registration step.

Final registration source digest: `d8d6e33172f002e37c4f5f789403db033d1c3019858d820e7bae063fe9d4b535`, in `M3-observation-registration-source-manifest.json`.
The source inventory still contains the same 66 files. I compared every final entry against the frozen implementation manifest and the actual working tree: the **only changed source-inventory entry is `.gitattributes`**. Every runtime, test, script, dependency notice/asset and scientific data file remains byte-identical to the independently replayed working-tree source. Committed text is equivalent under Git's CRLF/LF normalization; this is not a claim that ordinary source-text blobs and Windows working-tree bytes have universally identical line endings.

The narrow new rule `TEST_EVIDENCE/M3-observation-* -text -whitespace` fixes a concrete raw-evidence archival mismatch: the tested CRLF source manifest had otherwise been stored by Git as normalized LF text. It preserves the actual tested/new evidence bytes rather than regenerating scientific results or rewriting the hashed main review. The original frozen manifests and implementation review remain unchanged in the working tree; their actual bytes are now preserved in the final commit. Older M2/M3-numbered artifacts are outside the rule. No runtime or scientific meaning changed, so broad test replay is unnecessary for this metadata-only delta.

## Literal artifact and identity checks

I directly retrieved registered files from `git show 983342a280b3580a9d8eaaa449034f96f150203c:<path>` and computed SHA-256. Every registered review, test report and final source manifest matches the literal committed raw bytes and current metadata hashes, without a JSON-normalization substitute.

| Registered artifact | Verified raw SHA-256 |
|---|---|
| Main independent implementation review | `29c3c48ca7e08768e73deafdcf01e1b165ec906cf8b6ec5f093018c45fb3d9e8` |
| Independent J01 results | `7dda525e141302ae18a5ae26da8382b553ffca15a3b4368092c4ea6a56fb6029` |
| Independent J02 results | `ca5f7df3a49de5472bc2e3dc0b1b0e1e9df434c7b1f808effe2227982d72a271` |
| Independent J03 results | `114aa681091a538c82c5f3ed376fd051edd5a71690f14698cb800e6f6e5ab548` |
| Independent J04 results | `bf1055b9b08aa985d24fe847efaa30b9e1e850e69264c79e4af58db173a02082` |
| Final registration source manifest | `c818145f72d52ce08c3b41bfccd6ae492fd1643f19395b277bdc980f5e1e2bd5` |

Each PASS row's persona, scenario, AC, reviewer `/root/observation_review`, actual implementation commit and named main/negative tests agree with JOURNEY_ACCEPTANCE and the reports. The registered cases are:

- J01: `e2e_j01_candidate_shortlist`; negatives `e2e_j01_invalid_sequence`, `e2e_j01_missing_measurement`.
- J02: `e2e_j02_humanize_variant`; negatives `e2e_j02_numbering_unavailable`, `e2e_j02_insertion_mapping`.
- J03: `e2e_j03_complex_comparison`; negatives `e2e_j03_unmappable_residue`, `e2e_j03_missing_confidence`.
- J04: `e2e_j04_developability_review`; negatives `e2e_j04_unit_mismatch`, `e2e_j04_unknown_assay_condition`.

J05–J08 remain PARTIAL and have no fabricated acceptance records or implementation commit assignments. F12/F13 map to P03/P04, J03/J04 and their ACs, implementation files, retained tests and independent review. The checker passes with **8 defined journeys, 13 traced slices, 4/8 complete engineering journeys and 8/16 prescribed negatives**. Source inventory, every current file hash, report statuses/names and artifact hashes were independently checked in addition to the checker.

## Preserved history and data bytes

I compared Git tree/blob identities against prior milestone commit `c834094b96eaf4d04aefefd04ed20a900c8afe13`. All **64 prior TEST_EVIDENCE artifacts** are unchanged as committed blobs; the deliberate exceptions are the human evidence index and active JOURNEY_ACCEPTANCE registration metadata. Historical M1/M2/M3-numbered results, manifests, reviews and screenshots are not overwritten by the new acceptance. New retained output uses the explicit M3-observation prefix, and pre-fix failures remain labelled historical failures.

Pinned 3Dmol source/license, Gemmi license and `fixtures/public/1MLC.cif` were checked against actual final committed bytes. The public coordinate file remains exactly `5536c79a3d73e09503f6a4d252bbca2dac5fa0e59b5424309f49cd0c34e8606e`; no archive data or prediction/measurement was regenerated by this registration. Experimental scale evidence remains separate from synthetic prediction/assay fixtures and human scientific validation.

## Documentation and mission consistency

PROGRESS, PRODUCT_ALIGNMENT in English/Japanese, both READMEs, KNOWN_LIMITATIONS, CHANGELOG, ADR-0007 and the evidence index consistently report J01–J04 engineering acceptance, four remaining journeys and unfinished M3/release/scientific/user gates. Historical F08/F10/F11 statements now identify their earlier stage rather than contradicting current J03/J04 status. The Japanese README footer was corrected from six remaining journeys to four. The English/Japanese explanation policy and curated terminology remain consistent.

ADR-0007's corrected priority arithmetic uses breadth2 for two affected journeys: F12 83, F13 79. F13 is explicitly second-tier; neither engineering prioritization nor test counts are presented as scientific utility or biological validity. The bounded native controls support the required observation action, not a new representation catalogue.

The preliminary J05 Benchling/HELM benchmark in SCIENTIFIC_UX is explicitly preparation for the next missing composition workflow. It claims neither an implemented assembler nor independent design approval or J05 acceptance. No new scientific definition, external data transfer, copied dependency, chemistry guarantee or scope reduction is introduced by that documentation.

No unresolved registration issue remains in the reviewed state. This PASS covers the actual source/evidence bindings and current scope reporting. It does not certify a portable binary release, every platform's exact source-text line endings, human scientific goldens, all eight researcher evaluations or final 8/8 + 16/16 acceptance. The next implementation priority remains J05's coherent source-component → whole-design → comparison → unverified-question action, followed by J06–J08 and the remaining release gates.
