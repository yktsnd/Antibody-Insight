# F30 independent numbered comparison review

**Verdict: PASS.** Signed by independent reviewer `/root/numbered_review` on 2026-11-12 JST. F30 covers P01, P02 and P03 and the corresponding J01–J03 acceptance criteria. This verdict covers the reviewed engineering slice and the named browser regressions.

I reviewed a byte-copied snapshot with an independent SQLite store per replay and no external requests. The 112-file checker digest is `ad5ac230aca7a2076e9a10d29c3d0ff57499409cfa5b8f79d3669b6742764952`. The supplemental manifest also identifies the public inputs, replay harness, traceability baseline and specification files outside the checker inventory. [Source manifest](source-manifest.json) · [Review input hashes](review-inputs.json)

## Public source replay

Chrome imported both public Fab candidates through the ordinary FASTA, mmCIF and ANARCI file routes. In the shared H-domain IMGT column 105, D44.1 selected raw index 97 and deposited label B:97. D1.3 selected raw index 96 and deposited label B:96. Each displayed raw sequence cursor matched its row's imported index. The second selection updated the workspace breadcrumb and its own structural viewer. Mixed heavy/light domains suppressed the table. A coordinate absent from one annotation produced a dash without an action. Both maps remained visibly unverified. The replay observed zero page errors, outbound requests and stored mutations during inspection. The rendered 1440 × 1000 view placed the table and its actions above the raw sequence cards. [Public pair result](public-pair-W.json) · [Rendered workspace](public-pair-W.png)

## Independent browser checks

- Two maps for one candidate and chain required an explicit choice. The table ordered asymmetric insertions as 111, 111.1, 111.2, 112.2, 112.1 and 112. Clearing the choice hid the comparison.
- A mapped IMGT position with missing source atoms remained selectable in its own sequence. The absent peer annotation had no button, and both structural viewers had zero selected atoms.
- At IMGT 112.2, the synthetic candidates used raw 4 and raw 5. Selecting the latter highlighted only its actual H-author:104 source atom. The exact second candidate, chosen map and 112.2 position reached the existing Design screen. An explicitly selected unverified alternative could be viewed and the design action refused it.
- The original snapshot showed the first candidate in the breadcrumb after a second-row selection and retained unrelated raw-index highlights after changing the selected chain. The same independent assertions passed on the revised snapshot. A chain switch cleared the stale sequence cursor. Inspection preserved the complete saved bundle and generated zero outbound requests and JavaScript errors.

The replay used a labeled synthetic coordinate and numbering fixture for these seven checks. [Independent browser results](independent-edges.json) · [Independent harness](independent-edges.cjs)

## Named acceptance and alignment

All eight named main journeys and all sixteen prescribed negatives passed in the same frozen source. The signed audit records the exact case names, fixture artifacts, checksums and process exits. [Named audit](named-audit.json)

The researcher can inspect which imported positions differ between the two displayed candidates and follow one position to its original coordinate or an eligible design handoff. The table reuses explicit map choices and native sequence/structure selection, keeping the E-to-W-to-D/R action coherent without a new scientific comparison algorithm. The largest remaining product gap is a continuous research replay with human-verified numbering and measured evidence linked to the actual material and acquisition event, carried through to a saved selection decision. The public pair verifies file, residue and structure identity. Human scientific validation, researcher task evaluation and Release 1.0 acceptance remain pending.
