# Source preflight for real comparison

2026-11-12 JST · P01/P02/P04/P06/P07/P08 · J01/J02/J04/J06/J07/J08 and their corresponding acceptance criteria.

## Structure and sequence

The deposited D44.1 and D1.3 Fab entries describe distinct mouse antibodies bound to hen egg-white lysozyme. Both have a 214-residue light chain and a 218-residue heavy chain in the deposited polymer sequence table. The D1.3 source has label asym A (author L), B (author H) and C (author Y for lysozyme). The published D44.1 primary copy uses A/B and distinguishes the additional asymmetric-unit copy. These are useful inputs for the next numbered comparison. Original assays for the structural specimens are still required for a decision using measured evidence. [1MLC](https://www.rcsb.org/structure/1MLC) · [1FDL](https://www.rcsb.org/structure/1FDL)

D1.3 was checked against the original [mmCIF](https://files.rcsb.org/download/1FDL.cif), SHA-256 `6b525be71aff6850ebc4d83e2df75e2e8cfffbe7a2e4b68adf1aff9987a4c25f`. The check used `_struct_asym` and `_entity_poly`. It establishes deposited identity and chain lengths.

The D1.3 FASTA contains the two canonical polymer sequences with headers `1FDL-A` and `1FDL-B`, SHA-256 `76a70677701aade96e173a71bc06feea6c3003717dc108304b575c6f2e3d97ba`. ANARCI 2026.2.13.2 and HMMER 3.4 produced a native IMGT file in an isolated local Linux environment, SHA-256 `fc19caed78df3b8319193525b23fcbf087ab83246e721f4202fc23d723898899`. The tool reported light-chain raw positions 1–107 and heavy-chain positions 1–116. Human review is pending.

A Chrome preflight on the F29 implementation imported the four ordinary FASTA records, both mmCIF files and both native numbering files through the file picker. Explicit A/B assignments produced 432 coordinate correspondences for each candidate. Each candidate's IMGT heavy-chain position 105 was selected through its own numbering record, at raw position 97 for D44.1 and 96 for D1.3. The app highlighted the matching deposited B-chain position for each. The 1440 × 1000 screenshot shows the research obstacle: the separate raw-index tiles and numbering selectors make the shared IMGT positions difficult to compare. The preflight recorded zero page errors and external requests. [Browser results](M9-public-pair-W.json) · [Rendered workspace](M9-public-pair-W.png)

To replay, prepare `public-fab-pair.fasta` by concatenating the canonical A and B records for `1MLC` then `1FDL`, with LF after each header and each uninterrupted sequence. Set `AWX_PAIR_INPUT_DIRECTORY` to the directory containing that FASTA, the `1FDL.cif` download and `1FDL-AB.anarci.txt`. The harness reads the retained 1MLC files from the checkout. Run `node TEST_EVIDENCE/M9-public-pair-browser.cjs` from the checkout with the Python and Playwright runtime. [Replay harness](M9-public-pair-browser.cjs)

## Measurement provenance

**NEEDS-EVIDENCE** for measured CSV and a real evidence-based decision. The study behind PRIDE PXD063887 identifies its paired IgG4 samples and reports the comparative thermal experiment. The PRIDE project lists paired original instrument and controller files. The two inspected controller files have wall-clock readings in `HH:MM:SS` and temperature/power columns. Specimen lots and a timezone-bearing acquisition event remain unverified after checking the published methods, PRIDE entries and controller files. PRIDE submission/publication times describe repository activity. Instrument RAW inspection is pending. [Study and methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC12142670/) · [PRIDE file index](https://www.ebi.ac.uk/pride/ws/archive/v2/projects/PXD063887/files)

| PRIDE controller file | Bytes | Downloaded SHA-256 |
| --- | ---: | --- |
| `20240904_EMR2_Fiala002_IgG4_2F8_HG_WT_2p5uM_20240904152428_rampdata.txt` | 175146 | `f48673f515d5f7fb136545085332fc2ed1d1f59126de6fb7cece21787d659c9e` |
| `20240904_EMR2_Fiala002_IgG4_2F8_L368A_2p5uM_20240905115849_rampdata.txt` | 279832 | `6005588a51a1073628c01d240e09b33c0d98a7f7a8327b3f4e31c242b3117cbd` |

The NIST MAM inventory describes reference and unknown samples as distinct aliquots of the same digest. It gives a June–November 2017 acquisition window and states that some raw file metadata were removed or altered for anonymization. The retrieved inventory SHA-256 is `77987444e7110af68d0c5eb803402980f9c5e3bc1ea6d3c56dda116bd517f9e0`. A byte-range probe returned the requested 4,096-byte tail of the first 8,012,009,680-byte archive. This establishes archive access. Acquisition metadata remains unverified. [NIST inventory](https://data.nist.gov/od/ds/mds2-2497/README_2022-09-06.txt) · [Data catalog](https://catalog.data.gov/dataset/mam-consortium-interlaboratory-study-raw-data)

The existing import requires a source record mapping each measurement to its actual Material/Construct, with lot, original unit and a timezone-bearing event time. A laboratory run manifest or an equivalent original record would resolve this dependency. [Measurement contract](../docs/MEASUREMENT_CONTRACT.md)
