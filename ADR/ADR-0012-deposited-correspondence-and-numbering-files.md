# Deposited correspondence and numbering files

F27 covers P03/P04/P08, J03/J04/J08 and their ACs. F28 covers P01/P02/P03/P04/P08, J01/J02/J03/J04/J08 and their ACs. The researcher needs to move from registered sequences to the exact residue in a coordinate file and a separately identified numbering domain.

## Coordinate correspondence

W uses the existing source model and chain assignment form. A researcher can derive a map from the retained mmCIF after assigning each target chain. The source polymer entity, all positions and the complete monomer sequence must agree with that exact target chain. The mapping uses the source label asym/entity/sequence keys and retains the actual author IDs. Missing atoms and positions requiring a conformer choice stay unavailable. The derivation marker makes the persisted map reproducible at export and reimport. The UI identifies the typed basis separately from a researcher-entered source name. Manual correspondence remains available for other files and incomplete source coverage. [wwPDB label sequence ID](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_atom_site.label_seq_id.html) · [wwPDB asym entity ID](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_struct_asym.entity_id.html)

## Antibody numbering

Import the normal ANARCI numbering text with its declared scheme, record/domain boundaries and original inclusive zero-based interval. The CSV output has no scheme column. The text format supplies the scheme directly and leaves failed records visible. Domain positions must match the declared molecule chain and interval exactly. Supported CDR3 insertions retain their original letters in the file and use the established IMGT decimal positions in the map. [ANARCI output specification](https://github.com/oxpig/ANARCI/blob/79f6c575056dedef86cb8f405ebb039197923eec/README.md) · [ANARCI numbering source](https://github.com/oxpig/ANARCI/blob/79f6c575056dedef86cb8f405ebb039197923eec/lib/python/anarci/schemes.py) · [IMGT additional positions](https://www.imgt.org/IMGTScientificChart/Numbering/IMGTnumberingAC.html)

Keep one immutable numbering file with UTF-8 text, digest, recorded tool version and allocations to actual maps. Validate the allocation, source coordinate conversion, selected target and supplied attestation on preview and save. Existing map eligibility applies. An unverified tool output can be inspected and a source-verified import requires the researcher's actual review record. The adapter reads files locally. Scientific output for the public fixture was generated in an isolated test environment with upstream ANARCI and HMMER.

## Verification

Replay ordinary FASTA, coordinate and numbering files through W, inspect exact selections and restore the project to a fresh database. Test same-residue offsets, mismatched label entities, alternate conformers, stale file bindings, changed schemes and false eligibility. Record independent results and keep scientific and researcher acceptance open until the required reviews occur.

Use the current build to restore an archive with a typed deposited map or an original numbering file. Earlier builds reject unfamiliar fields and entity types during import.
