# ADR-0003 Imported antibody numbering and observation

- Status: APPROVED. Design and implementation PASS in TEST_EVIDENCE/M2-numbering-design-review.md and TEST_EVIDENCE/M2-numbering-independent-review.md.
- Date: 2026-11-02, Asia/Tokyo. Owner: implementation agent.
- Related: P01/P02/P08, J01/J02/J08, AC-J01/AC-J02/AC-J08; M2, F07.
- Problem: raw sequence positions cannot be displayed as IMGT positions or used to infer CDRs. Researchers need source-bearing imported numbering, explicit domain identity, failure states and a reproducible CDR-H3 grouping.
- Choice A: import externally assigned, source-bearing maps, check sequence/coordinate consistency and expose recorded verification status; derive IMGT regions only under a named supported domain definition.
- Choice B: invent numbering from raw indexes or install an unvalidated automatic assignment model immediately.
- Decision proposed: A. Automatic assignment is not necessary to meet the specified verified-numbering import scope; it remains a separate future adapter.
- Scientific sources: IMGT numbering and FR/CDR definitions listed in docs/NUMBERING_CONTRACT.md. Source coordinates are not inferred; structural residue identifiers remain a separate later relation.
- Security/identity: no external service, no sequence transmission, no data rewrite. Map IDs remain separate from molecule/chain/domain/coordinate identity. Exact source version/verification attestation are retained.
- Compatibility: add `residue_map` entity to awx/1. Existing graph-free and graph-defined records remain unchanged. Unsupported schemes/definitions are rejected explicitly.
- Fixture provenance: add optional Project.data_class (research/synthetic_fixture), preserving old projects without rewriting them. Title text never enables fixture numbering. Partial domains lacking104/118 anchors cannot supply a complete CDR3 group.
- Priority: required M2 observation prerequisite for J01/J02/J08, not an unrelated convenience feature. Mandatory gates: identity/provenance/security/regression; engineering scope adds no biological precision claim.
- Independent review: F07 implementation PASS, 159 Python tests and 5 F07 Chrome checks. Retained foundation assertions passed with the separate artifact-write error documented. Full M2 and final journeys remain pending. User confirmation: only if review exposes a changed scientific definition or target scope; not required for implementing the specified import.
- Rollback: isolated fixture DBs; keep old immutable records; do not integrate without independent PASS.

## F07 action and tests

Action: E previews/imports maps with sequences; W shows chain/domain, raw index, IMGT coordinate, region and source; E groups by an explicitly identified heavy-chain CDR3; state remains across screens.
Input/output: awx/1 maps and derived observation views; persistent original IDs and coordinate strings after restart/export/reimport.
Entities: Molecule and ResidueMap. Non-goals: numbering inference, numbering-scheme conversion, biological sequence validation, numbered variant creation, structure correspondence and complete J01/J02/J08 acceptance.

Happy test: an engineering fixture includes two chains with equal numeric IMGT positions and insertion positions in one chain. Imported domain IDs, source/verification state, CDR region and exact raw-index-to-coordinate relation remain distinct; explicit map selection resolves multiple versions. CDR3 grouping retains the full sequence and selected IDs.
Negative tests: (1) duplicate coordinates, wrong amino acid, bad insertion code or non-integer index reject without writes; (2) unavailable/failed/unverified/ambiguous maps do not become successful verified numbering or silently produce a CDR-H3 group.
The full J01 test still requires 800 candidates, assay-aware sorting, two-candidate comparison, five-candidate selection/reason/evidence and restart. The full J02 test still requires variants and saved reasons in M3.
