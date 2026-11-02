# ADR-0002 Explicit molecular composition and lineage

- Status: APPROVED. Independent implementation and M1 engineering gate PASS in TEST_EVIDENCE/M1-composition-independent-review.md.
- Related: P02/P05/P08, J02/J05/J08, AC-J02/AC-J05/AC-J08; shared M1 identity foundation.
- Owner: implementation agent. Date: 2026-11-02, Asia/Tokyo.
- Problem: a chain list does not express ordered domains/linkers, stoichiometry, binding-unit origins or parent/child changes. The full M1 gate and later J05 require these relationships.
- Option A: retain chains as the sequence representation and add a validated, explicit component graph plus independently identified binding units and lineage records.
- Option B: replace existing molecules and infer their topology from sequence or format names.
- Choice: A. B would infer unsupported science and break existing data. No molecular identities are collapsed or reclassified.
- Priority: mandatory foundation work. Identity, provenance, confidentiality and regression are mandatory gates; discretionary scoring does not displace this missing foundation.
- Compatibility: existing awx/1 bundles and databases remain readable without rewriting saved entities. New molecules may include `component_graph`; absent graphs mean composition undefined. Existing readers reject new fields/types explicitly rather than discard them. No existing entity is mutated.
- BindingUnit: separately identified, source-bearing chains and declared paired/single-chain topology. Chain origins may reference an exact interval in an existing molecule. References do not establish experimental binding.
- Graph: ordered components within each chain, an explicit copy count, and declared inter-component connections. Concatenated component sequences must equal the corresponding chain sequence. Source-backed components must match the referenced interval of the identified binding-unit chain. No linker, bond, pairing or stoichiometry is inferred.
- Lineage: immutable parent/child IDs, reason and exact before/after composition signatures. Cycles and duplicate parent/child edges are rejected. Parent measured evidence remains on the original Material; lineage creates no child measurements.
- Scientific interpretation: validates the consistency of supplied design metadata only. Does not validate folding, assembly yield, binding, disulfide chemistry or prediction applicability.
- Security/licensing: no added packages, network services or outbound requests. Same local storage and transaction controls.
- Tests and rollback: F06 below; retain all 55 foundation tests and browser replay. Changes stay unintegrated until independent PASS. Old entities require no migration; use isolated fixture databases for tests.
- Reviewer: design PASS in TEST_EVIDENCE/M1-composition-design-review.md. User approval: not required for implementing the already specified identities without changing their semantics; escalate if review identifies a meaning change.
- Re-review: scientific topology inference, automatic bonds, mutational numbering, incompatible interchange or external sharing.

## F06 implementation contract

Related: P02/P05/P08 / J02/J05/J08 / AC-J02/AC-J05/AC-J08.
User action: preview and import explicitly declared binding units, graph-defined molecules and lineage in E; inspect their ordered composition and origin IDs in W; export and reimport into an empty database.
Visible result: stable unit/molecule/chain/component IDs, order, copy counts, declared connections, origins and immutable before/after differences.
Input/output: awx/1 JSON; unchanged IDs and metadata after restart/roundtrip.
Entities: BindingUnit, Molecule, Lineage plus existing Construct/Material/Evidence.
Non-goals: an interactive assembler, numbered mutations, structure prediction, experimental validation or passing the complete J02/J05/J08 journeys.

Happy path: two source binding units form an ordered two-specificity molecule; save/restart/export/reimport retains order, declared copy counts, connections and origin IDs. A composition-change child has an immutable parent edge and no copied measured evidence.
Negative paths: (1) missing/duplicate chain or component ID, sequence mismatch, wrong-unit source interval or undeclared topology is rejected atomically; (2) a lineage or provenance cycle, wrong before/after signature or cross-project origin is rejected without any inserted records.
Additional independent cases are required by the reviewer.

Mandatory gates: preserve identities; retain explicit sources and unknown states; no outbound transmission; all prior invariant/browser tests remain passing. Full M1 is not PASS until the independent implementation replay covers this added contract.
