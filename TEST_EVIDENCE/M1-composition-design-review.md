# F06 composition and lineage: independent design review

Verdict: **PASS for the proposed F06 design**.
Implementation verification: **NEEDS-EVIDENCE**; no F06 product code existed at this review.
Full J02/J05/J08 and Release 1.0 remain incomplete.

Reviewer: `/root/independent_review`, separate from the implementation agent.
Date: 2026-11-02, Asia/Tokyo.
Reviewed baseline: `ab6f4d6f22fe73396b1cb455fecc63b74239c8fd` plus uncommitted ADR/ADR-0002-component-identity.md and docs/COMPONENT_CONTRACT.md.
Requirements: PRODUCT_GOAL.md; DEVELOPMENT_PLAN.md chapters 6/J02/J05/J08, 7 and 9; AGENTS.md; existing M1 data contract and previous independently verified foundation boundary.

## Traceability and visible action

P02/P05/P08 → J02/J05/J08 → AC-J02/AC-J05/AC-J08, limited to F06 identity/composition/lineage storage and observation.
User action: E previews/imports locally declared units, molecular components and parent/child composition changes; W exposes exact identities/origins; E exports/reimports.
Input/output: awx/1 JSON with persistent entity IDs, ordered component metadata, source intervals, connections and immutable signatures.
Entities: BindingUnit, Molecule, Lineage, with existing Construct/Material/Evidence relations preserved.
Non-goals: automated pairing, format classification, numbered mutations, chemical plausibility, folding, binding validation, copy-specific physical bonds, prediction applicability, interactive assembly or complete journey acceptance.

## Domain decision

The proposal implements existing required identities without changing their meaning. No mission, persona, four-screen architecture, local/no-outbound default, data sharing, licensing or scientific evaluation rule changes are introduced. No new requester approval is required for this documented implementation detail. A later feature that infers topology or claims biological assembly validity would require a fresh scientific/approval review.

BindingUnit is separately identified and source-bearing. Paired versus single-chain topology is declared explicitly; it is not inferred from sequence equality or chain labels. An independently supplied sequence may have no origin. A source-derived chain must retain the exact named Molecule/chain and inclusive raw sequence interval; matching sequence is a consistency check, not an identity rule or evidence of binding.

The graph preserves ordered components, roles, copy counts, sequence concatenation and declared intercomponent connections. Connection endpoints are scoped by molecule chain and component ID. For repeated chains the connection describes definitions, not individual physical copies. The existing limitation must remain visible: this graph may intentionally leave copy-specific assembly unresolved and must not be rendered as experimentally verified or fully specified atomic connectivity.

Lineage has immutable typed parent/child identities, an explicit reason and exact before/after signatures. It neither inherits Material measurements nor changes their subject. Requiring different signatures is appropriate for the current composition-only change set; metadata-only revisions and numbered substitutions are separate future contracts.

## Mandatory gates

| Gate | Design result | Required implementation evidence |
|---|---|---|
| Identity | PASS | BindingUnit distinct from Molecule; ordered chains/components and IDs preserved; copy counts explicit; source references use exact typed/project IDs; no equal-sequence collapse |
| Provenance | PASS | Actual source/version or honest unknown version; exact source intervals; provenance DAG and lineage DAG validated; exact immutable signatures; parent measurements remain on original Material |
| Security | PASS at design level | Same loopback/transaction/escaping/request controls; no additional dependency or outbound path; adversarial metadata remains text |
| Regression/compatibility | PASS at design level | All previous 55 tests/browser checks retained; old awx/1 bundles load and export without adding a null graph or rewriting entities; unknown new types/fields reject in old readers |

F06 is mandatory missing foundation work under the plan's scoring exception. This PASS does not authorize unrelated features or count any full journey as passed.

## Implementation details to enforce

1. Use strict non-boolean integers for copies/start/end; enforce the declared bounds, `1 <= start <= end <= source length`, and unique chain/component IDs in the stated scopes. Do not normalize invalid intervals or substitute an empty sequence.
2. Validate all origin and connection endpoint types/project identities/existence before dependency traversal. A corrupt reference must raise a validation error, never produce a partial insert or an unhandled traversal exception.
3. Define duplicate undirected connections by the unordered endpoint pair plus kind. Reversing left/right must not create a second identical connection. Distinct declared kinds can be retained without implying that their chemistry has been validated.
4. Keep provenance and lineage dependency semantics explicit. Provenance follows the stated Molecule → BindingUnit → origin Molecule references; lineage follows parent → child. Test each DAG without accidentally rejecting a legitimate child that derives components from its parent merely because the two relation types use different directions.
5. Compare before/after signatures using the existing JSON/type-aware approach, including nested arrays, sources and integer/boolean distinctions. An absent graph becomes null only in the comparison signature; the original stored molecule remains untouched.
6. Publish supported topology/connection enums and reject unknown values explicitly. Unsupported topology remains unsupported; do not infer a paired unit or invent missing components/copies/contacts to force acceptance.

## Independently proposed replay cases

The happy path is the declared two-unit composed molecule and composition-change child, with persisted/restarted/exported/reimported order, copies, origins, connections, parent edge and no child measurements. Add at least these independent negatives to the proposal's existing cases:

1. **Ambiguous equal sequence, distinct origin:** two BindingUnits have identical chain sequences. A component explicitly references the second unit and a particular repeated source interval. Roundtrip must retain that exact unit/chain/interval rather than replace it with the first matching sequence. Changing only origin identities changes the signature and must remain reviewable.
2. **Connection reversal and scope collision:** two different chains reuse the same local chain/component labels where permitted. Valid scoped endpoints resolve correctly; an endpoint with the wrong chain rejects. Adding the reverse of an existing same-kind edge rejects atomically; `copies=True` also rejects.
3. **Cross-kind provenance cycle:** molecule A component derives from unit B, whose chain origin names molecule A. Reject the whole batch even though both source sequences match. An acyclic child → unit → parent combined with parent → child Lineage must remain valid.
4. **Hidden signature tampering:** alter only a nested origin interval, copy count, component order or boolean/integer value in the stored before/after signature. Reject the lineage while leaving all previously stored entities unchanged.
5. **Old bundle byte-content preservation:** import an original graph-free awx/1 fixture, append new units/graph-defined child/lineage, restart and export. The original molecule's JSON content must be unchanged, including absence of `component_graph`; its original Material evidence must still target that Material exclusively.
6. **Boundary and depth:** reject intervals 0, reversed, past-end, boolean and floating-point indexes; allow an exact first/last-residue interval. Test a long acyclic dependency chain and a late cycle within the documented input limit so recursion depth cannot silently undermine atomic validation.

## Passage boundary

F06 may proceed to implementation and tests. Independent review must then inspect the actual code and replay import/inspection/restart/roundtrip plus the new negative cases before integration. F06 design PASS is not a full M1 implementation PASS. Human-validated scientific golden fixtures and complete J02/J05/J08 interactions remain required at their existing gates.
