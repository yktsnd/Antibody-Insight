# Independent research entry and conventional FASTA review

Reviewer: `/root/draft_entry_review`, separate from the implementation author. Date: 2026-11-10. **PASS for the bounded engineering entry and explicit multi-chain registration.** Human first-use acceptance, real source-traceable assay/design/decision work, scientific correctness and final frozen eight-journey integration are **NEEDS-EVIDENCE** and are not established by these replays.

Trace: P01/P02/P07, J01/J02/J07, AC-J01/AC-J02/AC-J07 for the paired synthetic entry; P01/P02/P08, J01/J02/J08, AC-J01/AC-J02/AC-J08 for ordinary FASTA record-to-candidate/chain registration. The scientific question is whether a researcher can inspect the intended H/L candidate rather than two accidentally separate sequence records, follow original samples and conditions, and retain a next experiment and selection rationale. Reusing the existing awx model, native import preview, W chain selector and R proposed Hypothesis/shortlist forms is a proportionate step; automatic pairing, another schema or a custom prediction engine would add unsupported assumptions.

I inspected the current adapter/UI implementation and independently ran two actual Chrome/temporary-SQLite paths. Source hashes before/after each run match and are embedded in each result. No production source was edited by this reviewer. Browser requests were restricted to the temporary local server, with no outbound requests or page errors. I inspected the resulting W/R screenshots. No existing research database was accessed or modified.

## Prepared synthetic example

`tests/research-entry-independent-browser.cjs` → `M6-research-entry-independent-v3.json`: six checks PASS.

- Empty E exposes the research question and one paired example. Preview cancellation via Escape leaves zero projects.
- Saving opens W with two selected candidates, each with H and L chains. Actual H/L differences are observable. Synthetic engineering numbering is labelled.
- R exposes original Material subjects, alternate material, distinct 25°C/37°C contexts and a missing thermal value. No computed evidence or prediction was added.
- A distinct proposed Hypothesis retains the exact original Evidence ID and next controlled experiment.
- W→R preserves the entered selection rationale and excluded evidence. The saved draft freezes exactly the reviewed original records and rationale, including the next action.
- Duplicate native import rejects atomically. An actual server stop/restart preserves saved Hypothesis and Decision records exactly.

Additional independent edges include cancellation, duplicate rollback, separate original conditions and null handling. The earlier v1/v2 results are preserved harness diagnostics: v1 tried the Close button hidden inside the previewed form instead of Escape; v2 required the word `collision` while the correct rejection said `Duplicate internal ID; no overwrite`. Correcting those assertions needed no application change. They do not demonstrate baseline product defects.

This replay has a known goal and scripted actions. It cannot satisfy the review's requirement that an unassisted first-time discovery researcher/project leader find the path and explain the saved reasoning, or establish comparative time savings. Those user observations remain open.

## Ordinary public sequence input

`tests/grouped-fasta-independent-browser.cjs` → `M6-grouped-fasta-independent-v2.json`: four grouped checks PASS, including multiple negative cases.

The test reads the real full Fab H/L sequences from the pinned complete public 1MLC source (`fixtures/public/1MLC.cif`, SHA-256 `5536c79a3d73e09503f6a4d252bbca2dac5fa0e59b5424309f49cd0c34e8606e`), writes an ordinary two-record local FASTA, and imports that actual file through the browser picker. It does not import a prepared awx project. The user explicitly declares candidate `D44.1`, chains H/L, roles heavy/light and Fab format. The resulting single molecular candidate has both exact source sequences and source digest/record-line references, with no fabricated experiments, numbering or structure.

The independent API path first enumerates both source records with zero registered candidates until assignments are supplied. Normal FASTA remains two unpaired candidates. Duplicate chain IDs within a candidate, stale source-text hashes, missing assignments and a boolean record index reject without writes. Browser duplicate-chain recovery succeeds after correcting the second chain ID. Changing source text or the target project returns blank declarations and disables saving; no original grouping leaks into a new scope. The v1 failed assertion examined numbering detail before selecting a residue; the corrected v2 explicitly clicks the residue and verifies the actual unavailable state. No application change was required.

This closes a narrow ordinary-data registration gap. It does not yet demonstrate ordinary-data structure correspondence, validated antibody numbering, real measured assays, variant design or an evidence-based final decision in one complete research task. FASTA source reconstruction remains the existing recorded digest/metadata boundary, not a claim that the original FASTA text is retained as a source-file entity.

## Product alignment and remaining gate

The paired example now lets a researcher practice inspection→sample/condition review→proposed next experiment→reasoned shortlist using existing screens. The independent public FASTA path establishes that user-supplied records can be explicitly grouped into a multi-chain candidate without inferred identity. The largest remaining gap is a complete real-data scientific action with validated numbering/correspondence and actual source-traceable measurements, followed by human scientific and researcher evaluation. Neither fixture success nor additional test count changes that gap or completes the product.

The observed UI still devotes substantial space to identifiers and one-molecule layout leaves the second column unused; those are existing lower-priority UX issues rather than grounds to widen this correction. The generic composition warning's phrase `Chain pairing ... not supplied` could more clearly distinguish detailed BindingUnit connections from the user's already-declared H/L grouping. These observations are not counted as failures of the bounded registration acceptance.
