# Public inputs for scientific review

The unmodified [3OGO](https://www.rcsb.org/structure/3OGO), [1VFB](https://www.rcsb.org/structure/1VFB) and [1FDL](https://www.rcsb.org/structure/1FDL) files come from the wwPDB archive. Archive data are CC0 under the existing [RCSB usage policy](https://www.rcsb.org/pages/policies). The accession pages give the corresponding primary citations.

The two FASTA files use canonical sequences from the deposits. The paired FASTA uses 1MLC A/B followed by 1FDL A/B. The 3OGO FASTA uses the entity sequence for label chain E. The original native tool outputs for the respective inputs were generated locally with ANARCI 2026.2.13.2 and HMMER 3.4 using the IMGT scheme. Read them alongside their deposited organisms and exact chain scope. Human validation is pending.

The candidate expectations are in [the scientific reference record](../public-structure-expectations.json). To replay the paired Workspace example, set `AWX_PAIR_INPUT_DIRECTORY` to this directory and run the [public-pair harness](../../TEST_EVIDENCE/M9-public-pair-browser.cjs) with `--numbered-comparison`.

`emicizumab-gsrs.json` is the public NIH GSRS record for UNII 7NL2E3F6K3, version 37, retrieved on 2026-11-13 JST. `emicizumab.fasta` extracts its four amino-acid subunits in source order. Q and J use the FDA review's names for the 448- and 444-residue heavy chains. L1 and L2 name the two separately recorded 214-residue subunits. [GSRS source](https://gsrs.ncats.nih.gov/api/v1/substances(7NL2E3F6K3)) · [FDA quality review](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2017/761083Orig1s000ChemR.pdf)

`nist-mam-reference-source.fasta` is the unmodified four-record [NIST MAM search FASTA](https://data.nist.gov/od/ds/mds2-2497/FASTA%20Sequence.fasta) from dataset `mds2-2497` v1.0.0, retrieved on 2026-11-13 JST. Only the first two records are NISTmAb subunits. The other two are database controls. [NIST terms](https://www.nist.gov/open/license) · [Reference expectations](../nist-mam-reference-expectations.json)
