# ADR-0004 Local structural observation with explicit correspondence

- Status: APPROVED. Independent design and F08 implementation PASS in TEST_EVIDENCE/M2-structure-design-review.md and M2-structure-independent-review.md.
- Date: 2026-11-03, Asia/Tokyo. Owner: implementation agent.
- Related: P03/P04/P08, J03/J04/J08, AC-J03/AC-J04/AC-J08; required M2 foundation, F08.
- User action: E previews/imports local PDB/mmCIF and explicit mapping JSON; W declares antibody/antigen chains, compares two structures, selects a real rendered residue or sequence position, follows source/confidence in R and preserves camera/navigation/restart context.
- Input/output: original coordinate text plus immutable structure/mapping records, explicit model/chain/residue keys, model-internal computed evidence. Export/reimport retains exact IDs, source, content and mappings.
- Entities: Structure, StructureMap, Molecule and computed Evidence. No identity is inferred from matching sequence or integer residue numbers.
- Option A: pinned Gemmi0.7.5 for local parsing, pinned locally served 3Dmol2.5.5 for actual interactive 3D rendering; keep correspondence in domain validation.
- Option B: hand-write PDB/mmCIF grammar and a new 3D engine. This expands unvalidated format/rendering code without helping the researcher workflow.
- Proposed choice: A. Retain upstream notices and unmodified dependency boundaries; application source remains Apache-2.0. Gemmi's MPL-2.0 package is installed as an external dependency, not copied into application code. 3Dmol's BSD-3-Clause and bundled notices accompany its pinned asset; explicitly select the included GLmol MIT option. No proprietary code or unknown license is introduced.
- Scientific boundary: author/label identifiers, models, insertion codes, alternate conformers and standard-residue consistency are explicit. No alignment, residue mapping, target identity, model confidence, folding or affinity is invented.
- Camera: preserve each structure's own centering and link orientation/zoom; label that this is not structural superposition. Do not claim aligned coordinate frames.
- Confidentiality: parsers/viewer run locally; no CDN, remote PDB lookup, analytics or remote model. CSP/network monitoring and all previous regressions remain gates.
- Compatibility: additive awx/1 Structure/StructureMap entities; old saved records stay unchanged. Structures have a declared primary Molecule; antigen target references are explicit namespaced external declarations, not inferred molecular IDs or experimental binding claims.
- Tests: local PDB+mmCIF parsing and exact raw roundtrip; full-source-digest validation; explicit model/chain/residue mapping; actual canvas click→sequence and sequence→3D; same orientation/zoom and restored view; computed score labels/missing confidence. Negative tests: unmapped/missing/ambiguous residues cannot highlight another atom; corrupt files, mismatched correspondence/digests and unknown references roll back atomically.
- Non-goals: structural prediction, automatic superposition, automatic alignment/numbering, biological confidence thresholds, complete J03/J04 (hypotheses/variants remain M3).
- Priority: missing mandatory M2 capability; identity/provenance/security/regression take priority over discretionary scores.
- Reviewer: F08 PASS, 207 Python tests plus retained11/numbering5/structure11 Chrome checks, all exit0. Full M2 and final workflows remain pending. Rollback: isolated fixture DB and source checkpoint; no rewrites/migrations. Escalate scientific/meaning or material license changes if independent review identifies one.
