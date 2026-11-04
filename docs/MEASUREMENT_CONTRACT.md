# Original measurements and expression constructs

Trace: F16/F17/F18, P06/P08, J06/J08, AC-J06/AC-J08. [ADR-0009](../ADR/ADR-0009-constructs-and-measured-evidence.md) defines the decision and tests. This adapter captures original declared results; it does not establish translation validity, expression causality or scientific comparability.

## Measurement CSV

UTF-8 input, comma separator, standard quoted multiline fields. Required header set:

```csv
material_ref,metric,value,unit,timestamp
```

Optional headers: `conditions_json`, `description`, and the paired `source_name,source_version`. Unknown/duplicate headers reject rather than being discarded. A malformed CSV rejects; invalid data rows are explicitly excluded in QC. Maximum 10,000 data records. Review the valid subset before saving; save revalidates all references atomically.

`material_ref` is the exact original token. A canonical known same-project Material ID resolves only to itself. Canonical wrong-type or unavailable IDs reject and cannot be remapped. Opaque external tokens require a file-scoped explicit mapping to an actual same-project Material. Case, whitespace, names, lots and equal sequences do not establish identity. Nonempty mapping requests must carry the SHA-256 of the exact submitted UTF-8 text; unused/stale mappings reject. Browser mappings remain in memory.

`value` is an empty/null scalar or a finite safe number in decimal-point notation. Zero is retained. No locale guessing, zero replacement, silent underflow, unit conversion or averaging. Qualifiers such as `ND`, `<0.1`, `>100` reject as point values; explicit curation may use an empty scalar with the original qualification in `description`. A non-null scalar requires an explicit original unit. Conditions are a JSON object or null; JSON numeric types are retained. Event time is the supplied timezone-bearing ISO 8601 `timestamp`, never import time.

When row source headers are present, each row supplies a nonempty source name and nullable version as a complete pair. Otherwise the explicit file-level source applies, defaulting only to the actual filename with unknown/null version. Row names never borrow file-level versions. `description` is retained as a source note. Repeated matching rows receive distinct IDs and a potential-repeat warning; equality is not evidence of independent biological replicates.

New Evidence is always `measured` and directly targets its actual Material. Optional `import_origin` contains `file_name`, `text_utf8_sha256`, one-based logical `record_index`, physical end `line_number`, original exact `source_material_ref`, and `importer` name/version. Header is before data records; multiline records can end later than their logical ordinal. This origin is separate from assay conditions and experimental source/version. The digest describes text actually submitted to the parser, including retained line endings/BOM, not arbitrary original encodings. JSON-imported origin is recorded attestation, not authenticated verification of an absent original file.

The browser retains the server-approved bundle JSON in volatile memory and rejects edits to a reviewed snapshot until another preview is requested. Fresh export downloads authoritative server JSON. This preserves integral float and signed-zero representations through the JavaScript UI without redefining the existing type-aware context policy. No scientific payload is written to localStorage.

## Declared metadata and comparison

Construct registration explicitly supplies actual Molecule ID, name, uppercase ACGTN CDS or null, recorded vector and signal metadata or null. Material registration explicitly supplies actual Construct ID, name and lot. Each creates a new distinct ID and optional actual local-entry `source` name/application version. This source describes the mechanism, not authenticated authorship or biological validation. Legacy records without the optional field stay unchanged.

Two selected Construct IDs must belong to the actual same Molecule. Raw DNA positional differences are unaligned one-based indexes; they are separate from amino-acid positions. Missing CDS on either side, including both sides, makes comparison unavailable. No chain/CDS pairing, translation, strand, synonymous mutation, signal processing or expression effect is inferred.

R shows separate original observations directly attached to the actual Materials in the Construct scope. Molecule/Construct-level records remain in their original evidence cards and are never repeated as Material observations. Measured/computed kinds, source/version, metric, unit and type-aware conditions define separate filtering contexts using existing F09 predicates. Unknown context remains inspectable but cannot join a known cohort. Researchers retain original Evidence IDs, proposed explanation, limitations and next controlled experiment using the existing Hypothesis workflow.

Engineering fixtures and independent agent checks do not replace the required human scientific golden review or researcher evaluation. J07 finalized decisions and full J08 prediction adapters remain separate unfinished work.
