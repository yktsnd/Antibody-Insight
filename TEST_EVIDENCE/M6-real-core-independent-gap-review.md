# Independent real-antibody core feasibility review

Reviewer: `/root/real_core_gap_review`, fresh review context. Date:2026-11-10. No production/source/fixture edits, database writes, private-data transmission, new dependency or dataset redistribution. This is a specification/source/primary-literature review, not a browser replay or human scientific acceptance.

**Plan direction: PASS. Complete real-data core feasibility/acceptance: NEEDS-EVIDENCE.** The revised plan9.2 correctly puts a continuous research action ahead of more features and separates prepared examples, own-file operation, scientific verification and researcher usefulness. Actual FASTA H/L registration is a useful first step; it does not remove the preparation needed for trustworthy correspondence, design and material-specific observations.

## Research action and first obstructions

The target is P01/P02/P03/P04/P07/P08, J01/J02/J03/J04/J07/J08 and their ACs: identify a candidate difference, inspect its source-resolved position, decide what to change or measure, and retain evidence/reasoning that another researcher can reconstruct. P05/P06 remain part of the final eight-persona goal; a single affinity case cannot stand in for their research questions.

1. **A public name is insufficient molecular/material identity.** [RCSB1MLC](https://www.rcsb.org/structure/1MLC) deposits D44.1 Fab. The [Lippow et al. primary study](https://pmc.ncbi.nlm.nih.gov/articles/PMC2803018/) measures single-chain antibodies displayed on yeast, using antigen titration and flow cytometry. Its Table1 includes wild-type affinity and mutant ratios. Those observations must not be saved as direct measurements of the deposited Fab's Material. Exact chain/domain/format/construct/sample correspondence is still required; sequence/domain similarity alone does not supply it. Ratios are not absolute mutant Kd measurements, and source-reported uncertainty must not become invented replicate data.
2. **Normal files still do not reach eligible design without prepared mapping.** `workspace_app/design.py::eligible_map` requires eligible numbering. `docs/NUMBERING_CONTRACT.md` supports the declared IMGT rearranged V-domain subset and requires genuine source-verification attestation, or explicitly synthetic engineering status in a synthetic project. The UI can inspect imported maps, but ordinary numbering output needs conversion to awx/1. PDB author position such as L92 cannot be relabeled IMGT92. A tool result cannot be described as human-reviewed merely to enable D. Manual residue-pair entry is also a substantial correspondence-preparation cost for a whole real antibody.
3. **Some real published metadata cannot honestly satisfy the measured importer.** `Material.lot` requires nonempty text; every Evidence timestamp requires a timezone-bearing instant. The [measurement contract](../docs/MEASUREMENT_CONTRACT.md) explicitly says event time is not import time. The consulted article does not provide a per-measurement event instant/actual lot identity in the inspected main text. Publication date or an invented midnight/timezone is not a valid substitute. Current measured-CSV validation correctly rejects missing required metadata, but this means the proposed public-paper case cannot simply be populated as local measured records. Whether source-uncertain dates/lots need an explicit richer representation is a separately reviewed provenance decision, not a hidden default.

## Smallest justified next work

- First assemble one source checklist for the actual input case: complete candidate chain/format declaration, original structural keys, the exact numbering source/version/interval and genuine review record, and actual Construct/Material/assay/event metadata. Choose a researcher-owned dataset with those records if available. Continue real sequence/coordinate observation with public1MLC separately; do not manufacture missing assay records to make one example cover every stage.
- Remove the prepared-awx bottleneck with a narrow, previewed adapter for an established numbering/correspondence output, retaining source keys and exact subject/chain/domain scope. Reuse Gemmi, existing validation/atomic import and E/W/D/R. Benchmark scientific tool interactions and check the selected tool/output/license before choosing a dependency. Do not introduce a new numbering algorithm, automatic pairing or an alternate mapping definition to make the example pass.
- Replay ordinary files through exact comparison, a justified substitution, a proposed next controlled experiment, original material observations and a reasoned decision. Record external-tool returns, remapping/retyping and source searches. Only the actual available stages may pass. If the chosen data lacks required metadata, keep that stage unavailable and retain the source uncertainty visibly; seek a provenance design decision before changing schema meaning.

An automated score, another dashboard or more prepared fixtures would not resolve these obstacles. The current four screens and distinct molecular/construct/material/evidence records should be retained.

## New edge cases for the next milestone

1. Same variable-domain sequence but Fab versus yeast-displayed scFv: imported observations must retain distinct subjects/formats/materials; they must not be copied or pooled as measurements of the Fab.
2. Paper reports date-only publication plus unknown assay time/lot: no UTC midnight, import-time measurement, fake lot, or fabricated source-verification reviewer; preserve an unavailable stage or explicitly approved literature representation.
3. PDB authorL92 and a valid IMGT position92 refer to different raw indexes: only the actual source conversion may select the intended residue; a bare integer match must not authorize a mutation.
4. A mutant/WT ratio with reported error and an absolute WT Kd: no silent derived absolute mutant point labeled measured, synthetic independent replicate, or discarded uncertainty. If later derivation is supported, preserve calculation provenance and its assumptions separately.

## 判定の要点

方針はPASS。実在抗体の中核経路全体はNEEDS-EVIDENCE。次の障害は、通常ファイルから利用できる番号・構造対応の準備と、測定結果が実際に属する分子形式・試料・条件の確認にある。D44.1という名称が同じでも、Fab構造に酵母表面提示の単鎖抗体の実測を付け替えない。日時・ロット・科学的照合の記録を作り足して成功例にしない。既存の保存・選択・出典の仕組みを使い、実資料が揃った一つの研究操作を次に通すことが最短の合理的な順序である。
