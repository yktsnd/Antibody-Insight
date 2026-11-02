# F08 preparation (not an implemented feature)

Current integrated source checkpoint: `6a5658e` (F07). Full M2, eight workflows and final acceptance remain pending.
The next change must declare P03/P04/P08, J03/J04/J08 and their ACs, happy path and two negative paths before implementation.

## Required behavior

- Import local PDB/mmCIF, validate before any persistent write and retain original source content/digest for roundtrip.
- Keep structure model, author chain, label asym ID where available, author residue number, insertion code and alternate location distinct. Do not map by integer residue number alone.
- Require explicit chain/residue correspondence to a molecule and raw sequence index. A matching residue letter is a consistency check, not evidence of molecular identity. Missing coordinates remain unmappable.
- Show antibody/antigen chain declarations, actual residue selection in both sequence and structure, and preserve camera across a two-structure comparison.
- Keep structural origin experimental/computed/unknown explicit. Do not derive pLDDT or other confidence from a B-factor field without a declared, source-verified convention. Missing confidence remains missing; model-internal metrics are not binding measurements.
- Test actual browser clicks on the rendered structure, not only direct calls to selection handlers. Verify unavailable mapping, no wrong highlighting, retained camera, original source and restart/export/reimport.
- Import corruption and unknown/malformed correspondence must leave existing data unchanged. Keep all earlier tests.

## Public primary resources already inspected

- [wwPDB coordinate format v3.3](https://www.wwpdb.org/documentation/file-format-content/format33/sect9.html): MODEL/ATOM/TER, chain/residue/insertion/alternate-location fields and coordinate units.
- [Gemmi model documentation](https://gemmi.readthedocs.io/en/latest/mol.html): PDB/mmCIF support, author versus label identifiers, source label_seq values and explicit sequence-assignment functions. Do not invoke automatic label-sequence assignment as if it were supplied source correspondence.
- [Gemmi distribution](https://pypi.org/project/gemmi/): stable 0.7.5 was observed. Its [license](https://raw.githubusercontent.com/project-gemmi/gemmi/v0.7.5/LICENSE.txt) is MPL-2.0. It is a candidate unmodified parser dependency, not installed or adopted yet. Any adoption must retain notices/source access and document the dependency boundary; do not change the application's Apache-2.0 license silently.
- [3Dmol viewer API](https://3dmol.org/doc/GLViewer.html): `modelToScreen`, `getView`, `setView`, `setViewChangeCallback` provide a possible local viewer/camera/physical-click-test path. The [project manifest](https://raw.githubusercontent.com/3dmol/3Dmol.js/master/package.json) showed 2.5.5; the [license](https://github.com/3dmol/3Dmol.js/blob/master/LICENSE) includes bundled-component notices. A pinned, locally served asset with retained notices is a candidate; no runtime CDN or download-by-PDB-ID behavior is authorized.
- [Official EMBL-EBI AlphaFold confidence documentation](https://www.ebi.ac.uk/training/online/courses/alphafold/inputs-and-outputs/evaluating-alphafolds-predicted-structures-using-confidence-scores/confidence-scores-in-alphafold-multimer/): model-score interpretation and limits. The future implementation still needs the relevant model/version's primary metric definition for each named field.

No parser/viewer dependency, structure adapter, confidence interpretation or scientific algorithm has been integrated by these notes. Resolve the schema and dependency choice in an ADR and independent review; do not replace the required structure workflow with a metadata-only substitute.
