# NIST Fab source preflight

2026-11-11 · Runtime at `405668c` · P03/P04/P06/P07/P08 · J03/J04/J06/J07/J08 · AC-J03/AC-J04/AC-J06/AC-J07/AC-J08

Can a researcher inspect a peptide-level observation in the context of a deposited Fab and retain the exact sample and measurement conditions behind a proposed experiment?

## Coordinate observation

**PASS** for the bounded Chrome replay using a fresh temporary database and a downloaded experimental mmCIF. `/root/deposited_mapping_review` independently re-ran all four checks and verified the file directly from RCSB. Both canonical sequences entered through grouped FASTA. The deposited light chain mapped all 213 positions with explicit label asym A, author chain L and the exact original coordinate keys. Selecting light-chain sequence position 30 showed label A:30. Reload retained the original file and map. There were zero page errors, outside browser requests or saved assay/construct/material records. [Independent browser report](M8-nist-fab-independent-browser.json)

The attempted full light/heavy correspondence rejected raw heavy-chain position 1 because the deposited residue is PCA while the canonical sequence reports Q. The failed preview saved no map. After saving the light-only map, selecting heavy-chain position 1 did not highlight a mapped coordinate. Deposited heavy-chain positions 224–227 have no resolved coordinates in the selected copy. An unmodified sequence, a modified deposited residue and an unresolved position represent different evidence. [PDB 5K8A](https://www.rcsb.org/structure/5K8A) · [Original mmCIF](https://files.rcsb.org/download/5K8A.cif)

Source SHA-256 `308fd5a6eb27eabdd7a398953e73eaa105c7980e40e582b723377fb445c2b4fc`.

## Measurement import eligibility

**NEEDS-EVIDENCE** for measured CSV and an evidence-based decision. The study identifies the measured Fab as an enzymatic preparation derived from Candidate RM 8670 lot 5F1b. The paper associates this Fab with 5K8A at the structural level. That does not identify the crystallography sample as the aliquot used for any particular HDX measurement. The study describes locally processed stocks, replacement kits and distinct controls. Individual acquisition instants and sample allocation records are required for the selected rows. [NIST data paper, sections 2 and 3](https://nvlpubs.nist.gov/nistpubs/jres/124/jres.124.009.pdf)

The downloaded centroid workbook SHA-256 matches the publisher's checksum `f425c9eb2a5bbca1a3a133473661050535c4c24bd75639d807b08474473e113f`. The independent reviewer `/root/real_core_gap_review` inspected all 60 worksheets and 108,670 nonempty cells. In the first centroid sheet, F1/O1 are exchange intervals, F2/I2 are relative days, F3/I3 identify runs, and D3/E3 label retention in minutes. No timezone-bearing measurement time was found. Workbook creation/modification times describe the document. Lab #1 cell F4 gives a centroid value for a charge-2 peptide without an explicit value-unit label at that cell. The reviewer flagged the need to confirm the reported scale and representation before importing numerical values as mass or deuterium uptake. [NIST centroid dataset and checksum](https://doi.org/10.18434/8SX3-NQ49)

1. An exact acquisition instant cannot be constructed from the exchange interval, relative day, run ID, retention time or repository timestamps.
2. A measurement of the prepared Fab cannot be assigned to an intact antibody, RM 8671, a crystallography sample or a different preparation from the shared sequence alone. Controls and Fc peptide rows retain their distinct scope.

The NIST MAM data are another source candidate. The published inventory documents a June–November 2017 acquisition window, distinct study sample roles and a tryptic digest of RM 8671 lot 14HB-D-002 for the reference. Exact time, offset and run-to-sample binding in the underlying raw files remain unverified. [NIST MAM inventory](https://data.nist.gov/od/ds/mds2-2497/README_2022-09-06.txt) · [Attribute analytics study](https://pubs.acs.org/doi/10.1021/jasms.2c00129)

## Product decision

Proceed under the current contract with original sample and acquisition records when available. The alternative is to add an explicit source-level statement for unknown or incomplete event time, carrying original labels as source text and preserving exact timestamps when supplied. It would retain legitimate observations without inventing dates. It would require reviewed rules for display, filtering, export and decision snapshots, and still require an actual material association and verified unit. A change to this provenance rule requires requester approval. [Current measurement contract](../docs/MEASUREMENT_CONTRACT.md)
