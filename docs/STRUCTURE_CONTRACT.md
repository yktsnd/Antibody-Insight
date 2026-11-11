# F08 structure contract

Related: P03/P04/P08 / J03/J04/J08 / AC-J03/AC-J04/AC-J08.
The authoritative source is the supplied coordinate file and explicit correspondence. Parsed observations do not establish that the assignment or biological model is correct.

## Immutable structure

`structure` (`stc_` UUID) has common fields plus `name`, `molecule_id`, `file_format` (`pdb`/`mmcif`), `content`, `sha256`, `origin_kind` (`experimental`/`computed`/`unknown`) and actual `source` name/nullable version.
The digest is SHA-256 of the exact stored UTF-8 text, not an unrecorded transformed file. File-byte encoding is normalized only by the explicit browser text read; the saved text is exported unchanged.
The molecule association is a user declaration, not inferred identity or proof of a complex.
The local parser validates finite coordinates/occupancy/B-values, supplied positive model identifiers, identifiable atoms and unambiguous residue keys. Missing mmCIF model IDs remain null and can be viewed as explicitly unknown; they cannot power explicit-model residue/chain correspondence or model-scoped scores. PDB's documented implicit single model remains distinct from this unknown CIF case. Up to100,000 atoms and24MiB coordinate text are initially supported; larger inputs report the limit rather than partial loading. Invalid or empty coordinate files reject before storage.
No automatic entity/sequence-ID assignment or coordinate transformation is performed.

Parsed residue identity retains `(model, auth_chain, label_asym, segment, auth_number, label_number, insertion_code, residue_name)`. Both author/label chain and number fields remain independently nullable; at least one source chain and one source number must exist. CIF unknown insertion/alternate codes remain null, distinct from blank/not-applicable. Alternate atom locations remain separate. Model numbers are not collapsed to a first model.
Missing label identifiers and absent/unknown segments stay null; an explicit blank/not-applicable segment is empty text. Quoted CIF dot/question literals are not missing markers and are rejected in numeric fields rather than converted to null. Unknown/modified residue parentage is not invented; only the20 standard three-letter amino-acid names are eligible for sequence-consistency mapping in this adapter, while other atoms can still be viewed.
Missing occupancy/B fields stay null, never parser defaults. Use Gemmi0.7.5 for syntax/structure reading and source CIF tokenization, with strict source-field checks; do not call entity/subchain/label-sequence assignment or first-conformer helpers. PDB hybrid-36 numeric identifiers are explicitly unsupported in this initial adapter rather than parsed as0. Reusing an identical model/author-chain/segment/residue-number/insertion locus across TER is rejected as ambiguous rather than merging distinct chain parts. Distinct post-TER residue numbers (including ligands/water) remain viewable; they are not automatically mapped to protein sequences. All supplied atom records are retained or the file is rejected.

## Explicit correspondence

`structure_map` (`smp_` UUID) has common fields plus `structure_id`, `molecule_id`, `source`, `chain_assignments`, `residues`.
The named molecule must equal the structure's declared primary molecule and be in the same project.
Each chain assignment has `model`, `auth_chain`, `label_asym`, `segment`, `role` (`antibody`/`antigen`/`other`), `molecule_chain_id` (nullable), `target_ref` (nullable `{namespace,identifier}`), and `label`.
Antibody assignments require an existing molecule chain and null target_ref. Antigen assignments require explicit target_ref and null molecule_chain_id. Other assignments require both null. The target reference is a supplied external identifier, not automatic identification or an assertion of experimental binding. The same reference across two structures is shown as a declaration with source.
Every assigned model/author/label chain must exist. Duplicate assignment keys reject.

Each residue entry has `chain_id`, `sequence_index`, `status` (`mapped`/`unavailable`), `structure_residue` (full key above or null), `altloc` (empty string or one-character supplied conformer), and `reason` (nullable).
Mapped entries require an explicit assigned antibody chain, an exact existing residue key, a represented chosen conformer (blank common atoms plus the chosen nonblank conformer), and a matching standard amino acid. A residue with multiple nonblank conformers requires explicit choice; no first-alternate fallback. Duplicate molecule-chain/index mappings reject. One structural residue locus cannot map to multiple sequence positions, even across different conformers or residue-name variants (microheterogeneity); separate maps may explicitly choose different alternatives.
Unavailable entries require null structure_residue, empty altloc and a nonempty reason. They never fall back to an equal integer on another chain/model or an adjacent observed residue. Unlisted positions are also unmapped.
Multiple maps/structures for a molecule require explicit selection. A map may cover one model; model identity is always part of its chain/residue keys.

## Confidence and rendering

Computed Evidence may directly target Structure; measured Evidence still requires Material. Structure→Molecule is a displayed declaration path, and evidence retains its original direct subject.
Known AlphaFold `ipTM`/`pTM` values, if supplied, are displayed as model-internal dimensionless computed metrics with source/version/time/conditions, not affinity or experimental measurements. They must have computed kind, unit1 and value in[0,1] or null. No pass/fail threshold is assigned. Missing confidence remains missing. B-values are shown as source B-values, never automatically relabeled pLDDT.
`conditions.structure_model`, when supplied, is a validated existing integer model ID. Without it, the score's model scope is explicitly unspecified/file-level, never repeated as each selected model's confidence.
Primary metric reference: official EMBL-EBI AlphaFold documentation linked in STRUCTURE_RESEARCH_NOTES.md; no model is run by this application.

The locally served viewer renders supplied coordinates, using stable local renderer IDs mapped back to full source keys. Atoms, ball-and-stick and C-alpha atom overview are display styles, not proof of chemical connectivity or secondary structure. Distance-based single bonds are a rendering aid, with incompatible/unknown alternate states and unknown elements excluded from bonds. C-alpha mode uses actual CA carbon atoms in standard amino-acid residues, with the selected source residue in atomic detail; no missing atoms or secondary structure are generated. Invisible atoms cannot be picked. Exact-source focus uses the selected atoms; an unmapped sequence position cannot reuse an earlier source selection. Source-only atom/residue selections retain their exact coordinate context without selecting an unrelated sequence index.
Link orientation/zoom while retaining individual centering. This does not superpose structures or make their frames equivalent. Persist only IDs, selected residue context and camera parameters; no coordinate arrays, sequence strings or score values are copied to localStorage.

## F08 acceptance evidence

Happy path: import two clearly marked synthetic complexes (one PDB, one mmCIF) with the same explicitly declared antigen reference and distinct candidate IDs. Show chain assignments, real3D canvas click and reciprocal sequence selection, preserve independent source keys and orientation/zoom, inspect computed confidence/missing confidence in R, restart and export/reimport exact source/map records.
Negative1: absent/ambiguous coordinate or mismatched chain/model/insertion/conformer cannot highlight a wrong residue. Negative2: corrupt file, wrong source digest, dangling/cross-project reference or non-finite coordinate rejects without changing existing records. Independent reviewer adds two further boundary tests.
F08 alone does not pass the complete J03/J04 journeys. Their saved hypotheses/design steps were subsequently independently replayed under F12/F13 in TEST_EVIDENCE/M3-observation-implementation-independent-review.md. Scientific/user/full release gates remain open.

## M6 source polymer order and legacy quarantine

New maps must preserve strictly increasing raw indexes versus source polymer order within a chain/model. PDB protein ATOM encounter order is used within exact MODEL/author-chain/segment/TER partition; author numbers and insertion codes identify residues and are never a sorting rule. Revisited non-contiguous source residues are unverified. HETATM-only or mixed nonpolymer positions do not prove polymer order. mmCIF uses a unique positive label_seq_id within model/label_asym_id, independently of row order and auth_seq_id. Missing/duplicate/ambiguous order retains an unverified record and withholds sequence/coordinate linking. Reversal is rejected after identity/AA/conformer/locus checks. This proves relative-order consistency, not a correct biological alignment or human scientific validation.

At read time the same assessment gates legacy map use. Contradictory/unverified maps produce mapping_status/mapping_warning, map=null and source-only coordinates. No database record is rewritten. A new Hypothesis cannot cite such a map as mapped context; exact source-only structure/residue hypotheses remain possible. Trusted existing records retain prior shape/reference checks while unrelated appends continue; newly supplied maps are always checked. No HTTP parameter exempts a new map. Export retains original maps, so fresh-store import rejects a contradictory legacy map rather than repairing it silently.

Primary definitions: [wwPDB v3.3 ATOM/TER](https://www.wwpdb.org/documentation/file-format-content/format33/sect9.html), [mmCIF label_seq_id](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_atom_site.label_seq_id.html). The requested correction changes no numbering scheme or residue identity.

## Deposited polymer positions

In W, assign the actual mmCIF source model and antibody chains to the exact registered chains. **Use deposited polymer positions** compares the complete deposited monomer sequence with each registered chain. It uses the explicit label asym, entity and sequence identifiers. The review lists mapped and unavailable positions before save. Missing coordinates and alternate conformers that need a choice are unavailable in this map. Manual correspondence supports an explicit alternate selection and other input files.

The saved map records its typed derivation and the coordinate file digest. Import rederives the entries from the retained source. W displays the derivation alongside the source label. Full-chain identity and exact coordinate keys establish the mapping for the retained file. Scientific interpretation and experimental comparability require their own evidence.
