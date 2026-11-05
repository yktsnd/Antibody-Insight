# Computed JSON import and transfer contract

F21: P03/P08, J03/J08, AC-J03/AC-J08. F22: P08, J08, AC-J08. See ADR-0011 and the independently reviewed domain/API reports under TEST_EVIDENCE/M5-predictions-domain*. Full frozen synthetic engineering replay and8/8+16/16 acceptance are independently verified at source commit a82cc0f3861bd24e89b2634ee2fe32826043be97; see TEST_EVIDENCE/M5-final-independent-review.md. M5 overall quality, standard performance and human scientific/researcher acceptance remain incomplete.

The researcher imports an original local JSON file in E, explicitly identifies its direct subject (Molecule, Construct, Material or Structure), reviews valid/excluded records, then saves new immutable records. W/R expose the actual source, value pointer and coordinate association. A full native project export reconstructs those records in a fresh store. No model is executed and no external run is authenticated. This fills a mandatory J08 gap; no discretionary feature score is used.

## Canonical computed-evidence/1

Root fields are exactly schema_version and records (1–10000). Every record supplies kind=computed, subject_ref, metric, value, unit, source{name,version}, timestamp and conditions. Optional description and residue_refs[{chain_id,sequence_index}] retain only their declared association. Event timestamps require a timezone. Source version/conditions may be null. Numeric values are finite safe JSON numbers or null, never boolean or qualified string points. Non-null values require their actual source unit. Conditions retain exact JSON types and signed zero; parameter metadata is not an application's scientific definition.

Unknown root/row/source/residue-reference fields reject the entire file with all escaped JSON pointers. Arbitrary conditions metadata is retained as supplied. Known-schema bad rows may be excluded from a reviewed valid subset; all original rows remain in the retained file. Empty/entirely invalid imports cannot save a source without results.

Application IDs, including apparent reserved prefixes, cannot be remapped. Otherwise exact external tokens may be explicitly bound to actual same-project subject IDs after preview. Whitespace, case and Unicode remain significant; names, sequence equality or lot labels never choose a subject. Mappings are bound to the exact submitted-text digest and cannot be unused or stale. The chooser displays each subject's actual type, full ID and construct/material/molecule path.

## Native alphafold3-summary/1

Explicitly choose an already registered computed Structure and a known positive model ID actually present in that coordinate file. There is no model1 default. A coordinate-model ID is separate from an external seed, sample, run or sample ranking. The association is the researcher's recorded assertion. Supply the actual computation source, original timezone-bearing event time, version or explicit unknown, and conditions or null.

Only documented scalar ptm, iptm, fraction_disordered (0–1) and ranking_score (-100–1.5) fields are extracted, dimensionless unit1. Preserve original metric names; absent fields create no result and null remains null. Any malformed recognized scalar rejects the entire summary. These are model-internal outputs, not measured binding or an application recommendation. All other original fields, including boolean/atom/token/chain/pair arrays, remain in the source and are listed as unmapped JSON paths. No flattening, averaging or scope reassignment is performed.

Parameter JSON travels from the browser as literal text and is parsed by the same strict server parser, avoiding client-side numeric normalization. Stored options require an object/null. Supplied structure_model must exactly match the selected actual integer model; it is never overwritten when conflicting. Unknown source versions are not invented or borrowed.

## Retained records and bounds

prediction_file (prf_ UUID) stores the complete submitted UTF-8 text (including a leading BOM and original line endings), filename, format, submitted-text SHA-256, bindings/options, importer/version/time and unique pointer→Evidence allocations. Computed Evidence records refer back using prediction_origin{file_id,json_pointer}. Both directions are validated on direct awx/1 import; expected scalar values, original numeric types/sign, context, source, subject and residue scope must agree. Hashes attest consistency of submitted text; they do not prove an external model run. Raw text is stored once. W/R load raw content and complete bindings/options/allocations into separate text-only detail views on demand and clear each when closed; the initial per-value view does not duplicate the full source allocation list. Source lookups reuse the existing cached entity index. Users can download the same submitted source text.

Input source limit24MiB; full JSON-escaped awx/1 project limit32MiB. Both atomic import and legacy shortlist append enforce the complete wrapper, never truncate. Existing larger records remain readable/exportable but cannot append beyond the limit. Malformed UTF-8, duplicate keys, nonfinite/unsafe/underflow numbers and unknown schema fields reject without writes. Proprietary source data remains local and scientific import drafts are not stored in localStorage.

New source records remain distinct from Structure and from computation Evidence. Existing FASTA/CSV adapters retained derived entities/provenance, not raw original files; transfer verification compares what they actually stored. Export includes all registered identities, source content, mappings, Lineage, proposed Hypotheses and immutable Decision versions. Reconstruction does not demonstrate computational reproducibility or biological validation.

## Verification

Happy path: actual FASTA→Construct/Material registration→PDB with explicit correspondence→measurement CSV→canonical and native computed JSON→W/R source/model inspection→two immutable Decision versions→restart→native export→fresh-store file reimport and exact typed Python comparison.

Prescribed negatives: duplicate-ID collision leaves every record unchanged; corrupt structure input cannot affect existing data. Additional domain/API cases cover wrong/foreign typed subjects, stale bindings, absent/experimental/unknown coordinate models, source/value/pointer/allocation tampering, all unsupported paths, null/zero/boolean/qualified values, malicious raw text, strict UTF-8, security/session/Origin/CSRF and JSON-escaped-size amplification. Independent reviewers propose and replay further edge cases. Only a frozen independent eight-journey replay registers final engineering acceptance; scientific goldens, researcher evaluation and other Release1.0 gates remain required.
