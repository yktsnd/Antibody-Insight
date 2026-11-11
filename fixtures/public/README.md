# Public experimental coordinate fixture

`1MLC.cif` is the unmodified PDBx/mmCIF data file downloaded on 2026-11-03 from [the RCSB data archive](https://files.rcsb.org/download/1MLC.cif). SHA-256: `5536c79a3d73e09503f6a4d252bbca2dac5fa0e59b5424309f49cd0c34e8606e`. Entry revision 1.3, 2024-10-23. [Entry and primary citation](https://www.rcsb.org/structure/1MLC); authors B. C. Braden, H. Souchon, J.-L. Eisele, G. A. Bentley, T. N. Bhat, J. Navaza and R. J. Poljak.

The archive data file is available under [CC0, per RCSB's data usage policy](https://www.rcsb.org/pages/policies). Website images and external integrated annotations are not included. No coordinates or source fields have been altered.

This is an experimental X-ray structure (2.50 Å), not a prediction or confidence fixture. Its asymmetric unit contains two Fab–lysozyme complex copies: light chains A/C, heavy chains B/D and lysozyme E/F (six protein chain instances, three unique protein entities). These are not merged by sequence equality. The local parser retains 8792 atoms and 1332 source residues, including 210 waters; 1122 are polymer residues. Water label-asym IDs G–L remain distinct from protein A–F and their shared author-chain letters. The test declares primary Fab A/B; C/D remain explicitly described other source copies, E/F declared lysozyme targets, water chains other. The source association does not redefine the entire asymmetric unit as one antibody molecule or biological assembly.

Mappings in `tests/public_structure_fixture.py` use deposited canonical sequences and explicit label sequence IDs, validating standard amino-acid agreement. No numbering, affinity, experimental measurement or confidence is generated. Tests use this checked-in file offline. This fixture verifies source preservation and antibody-scale observation; it does not replace scientific golden validation, two-candidate prediction journeys or researcher evaluation.

## Native numbering output

`1MLC-AB.anarci.txt` is the original numbering output generated on 2026-11-11 for the deposited full sequences of chains A and B in the pinned file above. The two FASTA headers were `1MLC-A` and `1MLC-B`. The isolated Ubuntu test used ANARCI 2026.2.13.2, HMMER 3.4, one CPU thread and the IMGT scheme. The public sequences were processed locally. [ANARCI package](https://pypi.org/project/ANARCI/2026.2.13.2/)

- File SHA-256 `26c2c44b388d7f62dd9efdf992a1c69f366f07cc0db1b43001e32c175c3e0747`.
- ANARCI wheel SHA-256 `8f88d49857abc2c5427c6cc903ebdac7b35e6636635eaa9d60bd8f0d4e7d14b7`.
- The source output covers A raw 1–107 and B raw 1–116 after converting the inclusive indexes. The raw HMM classifications are retained as tool output. Human scientific verification is pending.

The upstream CLI did not pass its explicit HMMER directory to the subprocess in this isolated run. The same package's `run_anarci` API produced the native text with an explicit local HMMER path. The workspace imports that file through its normal file picker.
