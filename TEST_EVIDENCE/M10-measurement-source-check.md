# Instrument metadata check for PRIDE PXD063887

2026-11-12 JST · P04/P06/P07/P08 · J04/J06/J07/J08 and their corresponding acceptance criteria.

**NEEDS-EVIDENCE for measured CSV.** The two public instrument files are identified by the [PRIDE file index](https://www.ebi.ac.uk/pride/ws/archive/v2/projects/PXD063887/files) and the [published experiment](https://pmc.ncbi.nlm.nih.gov/articles/PMC12142670/). The inspected version-66 RAW ranges contain acquisition-computer clock readings. The corresponding file-info clock fields are zero, and sample name, ID, comment, user-label and vial fields are empty in both sequence rows. The file-info run pointers matched the run-header locations reported by OpenReadout 0.4.0. Searches for an explicit lot/batch token in the bounded run headers found none.

| Original file prefix or range | Bytes read | SHA-256 of bytes inspected |
| --- | ---: | --- |
| WT prefix, interrupted original download | 4,191,782 | `5944421eb10162336f703731f965b128f0f2dc0a20f7414bcc205b1f2c73a037` |
| L368A prefix, bytes 0–262143 | 262,144 | `f538f644c526d07bb50734bd2c95aafe9468cf4fbdc81bd95d98f74e1f317e4c` |
| WT bytes 66390000–66455535 | 65,536 | `fd99b9402c85d8beb1277208b30f21fa2dadf8104b282c1a27e2eb06e2819a33` |
| L368A bytes 106608000–106673535 | 65,536 | `40780ce8daf67cb9bbdc6d7f8a752c8caf4b527477c2f5353ef8bcc374c66977` |

The local audit stamps read 2024-09-04 15:24:28.159268 and 2024-09-05 11:58:49.226841. The header layout describes these audit stamps as local clock values and distinguishes the separate file-info time. The ranges establish neither the UTC offset nor the original production lots. The metadata-only probe does not establish whole-file integrity or validate the thermal assay result. [OpenReadout format reference](https://openreadout.github.io/openreadout/formats/thermo-raw.html#file-header-offset-0-1356-bytes)

To use these runs in a measured comparison under the current contract, obtain a source manifest that identifies the original materials and lots and confirms the acquisition instants with offsets. A lab export linking each run to its source measurement could provide that evidence. [Measurement contract](../docs/MEASUREMENT_CONTRACT.md)
