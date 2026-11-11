# Imported IMGT numbering contract (proposed)

Primary sources checked on 2026-11-02:

- [IMGT unique numbering](https://www.imgt.org/IMGTScientificChart/Numbering/IMGTnumbering.html)
- [IMGT FR/CDR definitions](https://www.imgt.org/IMGTScientificChart/Nomenclature/IMGT-FRCDRdefinition.html)
- [Lefranc et al., 2003](https://pubmed.ncbi.nlm.nih.gov/12477501/)
- [IMGT V-DOMAIN numbering](https://www.imgt.org/IMGTScientificChart/Numbering/IMGTIGVLsuperfamily.html)
- [IMGT additional positions](https://www.imgt.org/IMGTScientificChart/Numbering/IMGTnumberingAC.html)

The initial supported definition is the IMGT **rearranged V-domain**, not the germline V-region or a constant domain. Unsupported definitions remain explicit rather than being reinterpreted.
The region intervals are FR1 1–26, CDR1 27–38, FR2 39–55, CDR2 56–65, FR3 66–104, CDR3 105–117, FR4 118–129. Inserted CDR3 coordinates remain part of CDR3.
FR4's endpoint follows the explicitly named FR/CDR nomenclature page, which gives129; another V-DOMAIN page has118–128 in prose. That discrepancy is recorded rather than treated as unanimous source agreement. No raw sequence residue is padded to reach either endpoint.

## Persistent map

`residue_map` has `rmp_` UUID, common fields, `molecule_id`, `chain_id`, `domain_id`, `chain_type`, `scheme`, `definition`, `status`, `reason`, `sequence_start`, `sequence_end`, `source`, `verification`, `entries`.

- `chain_type`: explicitly `heavy`, `light` or `unknown`, without inference from sequence or names.
- `scheme="IMGT"`, `definition="rearranged_v_domain"`; other definitions are not yet supported.
- `status`: `mapped`, `unavailable`, `failed`. Failed/unavailable records have no entries, null sequence interval and a non-empty reason. They never count as successful numbering.
- A mapped record has a valid inclusive raw sequence interval and an entry for every sequence residue in that domain, with no duplicate/missing raw indexes. The interval is declared by the source, not detected automatically.
- An entry is `{sequence_index, aa, number, ins_code}`. `number` is an integer from 1 to 129; `ins_code` is empty for ordinary positions or `.1`, `.2`, etc. at 111/112. The original coordinate identity is stored as this pair; it is never parsed as a floating-point number. Raw sequence index, IMGT position and PDB author numbering are distinct.
- This adapter initially supports the111/112 decimal extension subset. Legitimate IMGT additions such as60.1 or84A are explicitly unsupported by this adapter, not declared scientifically invalid. Their import reports an unsupported-position error; later support needs its own source-based tests.
- Entries follow sequence order. Numeric position gaps are permitted; missing positions are not fabricated. Additional positions at 111 are in ascending extension order, while those preceding 112 are in descending extension order. Duplicate coordinates reject.
- Extension suffixes are integer-ordered (`.2` before`.10` at111, reverse at112), never lexically or as floating-point values.
- Each amino acid must match the explicitly named molecule/chain/raw index. A map cannot silently attach to another same-sequence candidate.
- `source` uses actual source name and nullable version. The application does not submit sequences to IMGT or another service.

## Verification and use

`verification` has `status`, `reference`, `reviewer`, `reviewed_at`.
Statuses are `source_verified`, `unverified`, `engineering_fixture`.
`source_verified` requires a nonempty source/reference and recorded reviewer plus timezone-aware review time; it is a supplied attestation, not an automatic scientific validation performed by this application.
An unverified record has null reviewer/review time. Fixture status is visibly labeled as synthetic and cannot be relabeled as human-validated golden data.
Consistency validation and independent engineering replay do not establish biological correctness of the source assignment.

W displays any imported map's status and provenance. Observation-derived grouping uses a mapped source-verified record, or an `engineering_fixture` map in a project explicitly marked `data_class="synthetic_fixture"`. Project title text alone does not establish fixture status or eligibility. Existing projects lacking the optional data_class field are treated as research data; old records are not rewritten. New ordinary projects default to research.
Unverified maps may be inspected but must not silently power source-verified numbering actions.
Full CDR3 grouping additionally requires mapped anchors104 and118 bracketing the complete contiguous observed raw-sequence interval. If either anchor is absent, the mapping remains inspectable but CDR3 is partial/unavailable and cannot become an empty or complete CDR-H3 group. Numbering gaps within an observed short CDR3 remain gaps, not invented residues.
If several eligible maps/domains exist for a chain or several heavy-chain domains exist in a molecule, the user must explicitly choose a map/domain. No latest/first match is silently selected for CDR-H3 grouping.
Grouping uses the mapped sequence's CDR3 residue order, never lexical sorting of coordinate strings or a raw-sequence substring heuristic.

The application validates imported data consistency. It does not perform numbering, assign humanness, validate antibody function or assert that fixtures are scientifically human-verified.

## Native ANARCI text

Choose **ANARCI IMGT numbering text** in E and import the output for an existing project. Match the exact record and domain to a registered candidate chain. Preview includes the tool's original H/K/L classification and the inclusive raw interval. A missing hit stays excluded with its source identifier. Save retains the selected maps and a single original UTF-8 file. W shows the verification state and can download the original bytes.

The parser requires the source's explicit IMGT declaration. It converts both inclusive zero-based indexes to one-based indexes and consumes a raw index only for a numbered residue. It retains the exact source text and converts supported ANARCI 111/112 letter insertions to the existing IMGT decimal coordinates. The actual chain sequence, order and map shape must pass validation. Other schemes and unsupported insertions are reported at import. [ANARCI file format](https://github.com/oxpig/ANARCI/blob/79f6c575056dedef86cb8f405ebb039197923eec/README.md) · [IMGT additional positions](https://www.imgt.org/IMGTScientificChart/Numbering/IMGTnumberingAC.html)

An immutable `numbering_file` holds the content, digest, recorded version and allocations. A `residue_map.numbering_origin` names the exact file, record occurrence and domain. Save and fresh import rederive the numbered entries and verify the target and review record. The preview requires a fresh binding when the source text changes. Use the optional scientific review fields only for an actual review covering those domains and chains. Unverified imports are available for W inspection. Eligible numbering-dependent design continues to require the existing recorded review.
