# Public inputs for scientific review

The unmodified [3OGO](https://www.rcsb.org/structure/3OGO), [1VFB](https://www.rcsb.org/structure/1VFB) and [1FDL](https://www.rcsb.org/structure/1FDL) files come from the wwPDB archive. Archive data are CC0 under the existing [RCSB usage policy](https://www.rcsb.org/pages/policies). The accession pages give the corresponding primary citations.

The two FASTA files use canonical sequences from the deposits. The paired FASTA uses 1MLC A/B followed by 1FDL A/B. The 3OGO FASTA uses the entity sequence for label chain E. The original native tool outputs for the respective inputs were generated locally with ANARCI 2026.2.13.2 and HMMER 3.4 using the IMGT scheme. Read them alongside their deposited organisms and exact chain scope. Human validation is pending.

The candidate expectations are in [the scientific reference record](../public-structure-expectations.json). To replay the paired Workspace example, set `AWX_PAIR_INPUT_DIRECTORY` to this directory and run the [public-pair harness](../../TEST_EVIDENCE/M9-public-pair-browser.cjs) with `--numbered-comparison`.
