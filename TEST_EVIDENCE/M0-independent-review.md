# Independent M0 design review

Reviewer: independent review agent `/root/independent_review`, separate from implementation agent.
Review date: 2026-11-02, Asia/Tokyo.
Repository base: `0fa83529cb04dfc3128730b8997d91c058424e1d`.
Reviewed material: uncommitted PRODUCT_GOAL.md, AGENTS.md, DEVELOPMENT_PLAN.md, TRACEABILITY.csv, docs/INITIAL_REVIEW.md, docs/ACCEPTANCE.md, docs/SCIENTIFIC_SOURCES.md, ADR/ADR-0001-local-foundation.md, followed by the newly supplied docs/DATA_CONTRACT.md, KNOWN_LIMITATIONS.md, docs/screen-prototype.html and TEST_EVIDENCE/M0-screen-prototype.png. The rendered image was visually inspected: E/W/D/R, fixture labeling, unavailable features and draft/final distinction are visible without clipping. No application code or executable acceptance evidence existed in this snapshot.

## Verdict and its boundary

- M0 specification/design milestone: **PASS** against the actual DEVELOPMENT_PLAN chapter 9 passage criterion: J01–J08 test procedures reviewed and mandatory term definitions sourced. The supplied model/data contract, ADR and static four-screen prototype support this design decision. This is a design milestone PASS, not evidence that the application or scientific golden dataset is complete.
- Initial M1 foundation **design review: PASS**. Implementation and testing of the declared initial slice may begin under the existing product rules. This does not verify an implementation, authorize integration of unreviewed code, or satisfy any full J acceptance criterion.
- Full M1 implementation and Release 1.0: **NEEDS-EVIDENCE**. No application or tests were available to replay. No 8/8 or 16/16 execution claim is supported.

The 18 human-validated scientific golden fixtures and researcher evaluation remain unfulfilled chapter 10 verification requirements, explicitly tracked in KNOWN_LIMITATIONS L01/L07. They are not an added pre-coding gate. Implementation work may produce engineering fixtures, but synthetic fixtures cannot become human-validated scientific fixtures by relabeling them.

## Scope and mandatory gates

Affected traceability: P01–P08 / J01–J08 / AC-J01–AC-J08 for the design; initial implementation F01–F05 as individually traced in docs/ACCEPTANCE.md.
User action: preview an import in E, explicitly save, observe selected identities and sequences in W, follow evidence and save a selection memo in R, restart and reopen the persisted result.
Input: locally supplied FASTA/CSV/awx/1 JSON, with explicitly labeled engineering fixtures for tests.
Visible result/output: validation/QC and conflict messages, distinct entity IDs, sequences, evidence type/source/subject paths, persisted memo, explicit JSON export.
Entities: Project, BindingUnit, Molecule/component graph, Construct, Material, Evidence; later Lineage, ResidueMap, Hypothesis and finalized Decision remain separately tracked requirements.
Non-goals: automatic molecular classification, invented chain pairing, IMGT numbering inference, structure correspondence inference, prediction execution, finalized J07 decision workflow, full AIRR/PDB/mmCIF support, completed eight-persona workflows.

| Gate | Design result | Required implementation proof |
|---|---|---|
| Identity | PASS: typed internal IDs, external IDs separate, matching sequence only flags duplication; Construct and Material remain distinct | Same protein/different CDS and same construct/different lot remain distinct across restart/export; complete reference validation |
| Provenance | PASS: measured/computed/literature/annotation remain distinct; hypotheses/decisions separate; measured targets Material directly | Reject unknown Material and malformed source/version/timestamp; preserve null conditions/values without zero substitution; no inherited child measured values |
| Security | PASS at design level: loopback, same origin, CSRF/session, CSP, explicit local data path, no outbound code/resources | Actual Host/Origin/CSRF/size tests, escaped hostile content, network monitoring, verified local default path and access behavior |
| Regression | PASS at baseline design level: no existing application implementation removed | Retain every added test; partial flows remain partial; later stages replay existing checks and the declared new negative cases |

Foundation work is the plan's mandatory foundation exception to discretionary scoring; this PASS does not authorize expanding scope through an invented feature score.

## Identity and provenance assessment

Material-only direct attribution for measured Evidence is consistent with J06 and the plan's Material ownership rule. Molecule-level presentation must show the Material → Construct → Molecule path and must not aggregate away sample identity. A file without a usable Material reference is rejected, not attached to a guessed Molecule. This is a safe restriction of the initial importer, not a claim that all future scientific measurements always concern only a single material.

SQLite transactions, immutable entities and no overwrite APIs are reasonable for the local initial implementation. Unknown-field rejection with a complete field-path list meets the requirement to expose unsupported fields. Internal ID collision must roll back the whole batch, including entities tentatively inserted before the conflicting row. Rejecting one batch must leave existing data and selection unchanged. Sequence equality must never collapse distinct molecular formats, constructs or lots.

No inferred numbering, role, format or structure mapping is introduced. `format=unspecified` and `role=unknown` must remain honest absence markers, with unsupported capabilities visible. Imported computed values must carry their actual source and version; no invented confidence or retroactive measured classification is acceptable.

## Eight journey definition replay

This is an independent requirements replay against DEVELOPMENT_PLAN.md, not a browser execution. The original plan remains authoritative where the shorter table omits a detail.

| Journey | Definition result | Future execution evidence that must remain explicit |
|---|---|---|
| J01 | PASS as a future test definition | 800 input records, duplicate and invalid-row QC, CDR-H3/binding grouping, two-candidate observation, exactly five persisted IDs/reason/evidence and null measurement behavior. Atomic import requires correction or explicit re-submission of validated records; do not silently discard invalid rows. |
| J02 | PASS as a future test definition | Parent unchanged, new child and mutation list, source-verified IMGT scheme/chain/insertion identity, CDR/FR display, reason and checks, no parent measured evidence copied to child. Numbering failure must remain failure. |
| J03 | PASS as a future test definition | Antigen/antibody chain correspondence, reciprocal sequence/structure residue selection, retained camera, model-specific confidence meaning and limits, persisted design hypothesis. Obtain the relevant model's primary metric definition before displaying ipTM or another named score. |
| J04 | PASS as a future test definition | Observed property ordering, warning-site structure context, separate measured/computed provenance and conditions, mutation reason and unverified hypothesis. Reject unconverted units and implicit merging of unknown conditions. |
| J05 | PASS as a future test definition | Ordered multi-chain/domain/linker graph, BindingUnit origin IDs and stoichiometry preserved after reload, comparison with another design, unsupported analyses blocked explicitly. No string-only molecular representation. |
| J06 | PASS as a future test definition | Two distinct constructs of the same protein, three distinct materials, correct per-material measured attribution/units/conditions, saved next-experiment question. No unknown-sample fallback or unconditional mixed-unit mean. |
| J07 | PASS as a future test definition | Three candidates, criteria/weight revisions, visible missingness and tradeoffs, navigation to original evidence, immutable finalized snapshot and explicit revision/export. Required-metric absence blocks finalization; a selection memo does not satisfy this journey. |
| J08 | PASS as a future test definition | FASTA/structure/CSV/JSON, original provenance/version/material and chain maps, full roundtrip comparison into empty DB including decisions, complete unsupported-field report. Duplicate IDs and corrupt structures cannot alter existing data. Initial awx/1-only roundtrip does not pass this whole journey. |

All eight rows and their two prescribed negatives remain present and traceable. Before an execution can PASS, each test still needs concrete input fixtures, exact expected IDs/values or stable comparisons, command/UI steps, target revision, complete logs and verifier. The prose matrix is adequate to direct that work, not to replace it.

## Implementation requirements and outstanding evidence

1. Implement the supplied awx/1 and CSV contract with strict field types/enums and required/nullable validation. The contract now defines typed/project references, timestamps, project-local external-ID collisions, supported versus planned entities, same-project append rules, and nested field-path rejection. Key presence alone is insufficient validation. BindingUnit and a full component graph remain explicitly pending, so a list of chains must not satisfy J05 or the full M1 molecular-composition gate.
2. Preserve honest source identity. Require actual tool/source name and version where available; for an unversioned local source file preserve its recorded identity or digest and explicit version absence rather than fabricate a scientific version. The source-version key must remain present. Document its nullable/file-identity semantics in the import examples before testing that case. Do not confuse import time with measurement/computation event time.
3. The contract now specifies commit-time validation after preview and atomic reference/conflict checking. Test that another tab inserting a conflicting ID after preview still causes complete rollback. Validation must cover references inside imported entity payloads, not merely the top-level row ID.
4. Retain KNOWN_LIMITATIONS L01–L10. Scientific fixture/evaluator evidence, computational mapping, full molecular graphs/lineage, final decisions, performance, all browser flows, researcher review and shared-user security remain unverified. There were no executable failure logs to inspect because the application/test suite had not been implemented.
5. Before accepting M1, independently review the actual diff and test output, replay initial user actions in a browser with persisted fixtures, and test the boundary cases below. This design PASS is not reusable as an implementation PASS.

## Independently proposed edge cases

These supplement, rather than replace, the prescribed 16 negatives.

1. **Cross-project reference poisoning:** import Evidence in project A naming a real Material in project B, or name a Construct ID where Material is required. Expected: typed/project-specific reference error; zero inserted entities; no evidence appears under either molecule.
2. **Late transaction failure:** a batch contains valid new Project/Molecule/Material records, followed by one colliding Evidence ID or one dangling subject reference. Expected: complete rollback, same existing row contents/counts, no orphan entities, successful later corrected import.
3. **Preview race:** preview valid input, commit a conflicting ID from another tab, then save the first preview. Expected: conflict at final commit and no partial write; no overwrite based on stale preview.
4. **Same sequence, different scientific identity:** two molecules with identical chain sequences but distinct declared component graphs, two CDS designs and multiple lots. Expected: no identity collapse; each measured value stays on its original material after export/import/restart.
5. **Null/zero and numeric validity:** preserve measured `0` as zero and missing value as null; reject NaN/infinity, numeric booleans, malformed timestamps or blank source identity according to the published schema. Conditions absent must remain unknown, never silently become an empty set of known conditions.
6. **Hostile imported text:** FASTA header or evidence source contains HTML/script and newline characters. Expected: safely rendered text, no script execution, no sequence-bearing server logs, no outbound request; stored original content roundtrips according to the contract.

## Primary-source check

Public sources were independently opened on 2026-11-02; no private sequence or experiment data was submitted.

- [IMGT numbering](https://www.imgt.org/IMGTindex/numbering.php) defines numbering for domain comparison; treating raw sequence indexes as unverified IMGT positions would be unsound. The current no-inference boundary is appropriate.
- [W3C PROV overview](https://www.w3.org/TR/prov-overview/) describes entities, activities and involved people. The present source/type/subject design is inspired by provenance principles and is not demonstrated PROV interchange conformance.
- [AIRR Data Standards](https://docs.airr-community.org/en/latest/datarep/overview.html) describes versioned typed schema specifications. awx/1 is explicitly a project schema and must not be advertised as AIRR conformance.
- [OWASP ASVS](https://asvs.owasp.org/) identifies stable ASVS 5.0.0 and a verification framework. Listed controls are proposed controls; no ASVS certification or implemented-security PASS follows from a design list.

No new scientific algorithm, molecular meaning, persona, primary screen, external sharing behavior or scientific validity threshold is approved by this report.

No additional scientific definition blocks the declared initial M1 slice: it imports declared metadata and provided evidence, and makes no numbering/CDR/structure/prediction calculation. Primary metric definitions and source-verified correspondence fixtures become prerequisites when those later scientific features are implemented.
