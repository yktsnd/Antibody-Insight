# Explicit composition contract

This extends the declared awx/1 entity vocabulary additively. Existing records remain unchanged and valid. It records the researcher's declarations; it does not infer a molecule's biological format from sequences.

## Binding units

`binding_unit` uses a `bnd_` UUID and common entity fields, plus `name`, `topology`, `chains`, `source`.
`topology` is explicitly `paired` (two chains) or `single_chain` (one chain).
Each chain has `id`, `role`, `sequence`, `origin`.
`origin` is null for independently supplied sequences, or an object containing `molecule_id`, `chain_id`, `start`, `end` (inclusive, 1-based raw sequence indexes).
An origin interval must exist in the same project and exactly reproduce the declared sequence.
These indexes are not IMGT positions. No binding or chain-pairing experiment is implied by the declaration.
`source` uses the existing actual name and nullable version contract.

## Molecular component graph

An existing `molecule` may additionally have `component_graph`.
An absent graph means composition undefined; it is not automatically completed from `format` or `chains`.
An explicitly present graph must be an object with `chains` and `connections`.

Each graph chain has `chain_id`, `copies`, `components`.
Every molecule chain appears exactly once; `copies` is an integer from 1 to 100.
Each ordered component has `id`, `role`, `sequence`, `origin`.
Component IDs are unique within the molecule. Concatenating the ordered sequences must exactly reproduce the corresponding molecule-chain sequence.
An origin is null for explicitly supplied components, or has `binding_unit_id`, `chain_id`, `start`, `end` and matches that binding-unit interval exactly.
Linkers and other unreferenced components still require explicit sequence and role; nothing is filled in automatically.

Each connection has `left`, `right`, `kind`.
Each endpoint has `chain_id` and `component_id`.
Both endpoints must exist, differ, and occur in a nonduplicate connection.
Kinds are `covalent`, `disulfide`, `noncovalent` or `declared_pairing`.
Connections are declarations between component definitions. Where a chain has multiple copies, they do not identify individual atomic/chain-copy contacts; the UI must state that limitation and must not render invented copy-specific bonds.
Chemical plausibility and assembly are not validated.

Provenance dependencies from a molecule to a binding unit, then to any origin molecule, must be acyclic. This prevents a sequence declaration from claiming circular derivation.

## Lineage

`lineage` uses a `lin_` UUID and common entity fields, plus `parent_id`, `child_id`, `change_set`.
Both molecules must exist in the same project, differ and define a nonduplicate acyclic parent→child edge.
The M1 `change_set` has `kind="composition"`, `reason`, `before`, `after`.
The exact composition signature is `{format, chains, component_graph}`; an absent graph is represented as null in the signature only, without modifying the molecule.
`before` and `after` must be exact JSON/type-aware copies of the named parent and child signatures and must differ.
Lineage does not copy Evidence, infer assay comparability, or change the direct subject of any measurement.
Numbered substitution change sets are a later extension with source-verified ResidueMap prerequisites.

## Scope limits

This section records the original M1 stored-composition boundary. Later independently reviewed stages added imported numbering, structural observation and full synthetic J02–J04. F14/F15 and full synthetic J05 subsequently passed independent review in TEST_EVIDENCE/M3-composition-implementation-independent-review.md. Scientific/user/release gates remain open.
Both scientific human-validated golden fixtures and the final release gates remain pending.


## F14/F15 recipe and source-usage views (independently verified engineering scope)

`composition_preview` accepts explicit name/external ID/declared format, chains (ID/role/copies/ordered components), declared connections, optional actual parent/reason and optional researcher annotation. A component has its own ID/role and a source: either `{kind: binding_unit, binding_unit_id, chain_id, start, end}` or `{kind: sequence, sequence}`. The server resolves only the exact source interval within the project. Empty/missing chains, copies, sequences, source references and endpoints reject instead of being completed. Accumulated chain length is checked before concatenation against the existing100000-residue limit. Connection cycles are permitted declarations; provenance/Lineage cycles remain forbidden.

A new independent composition has no invented parent or lineage reason. An explicit parent requires a reason and an actual changed composition signature. Optional notes become researcher annotation Evidence with null scalar/unit/conditions and actual local-entry provenance, not a measured result or computed score. No Construct/Material/measurement/structure/numbering is inherited. The preview returns new immutable records for the existing atomic import. The UI review route additionally returns the derived source context before saving; it remains read-only and uses the same session/Origin/CSRF/strict request validation.

`composition_context` preserves each actual source unit/chain/interval/component instance and declared copy count. Full source-chain occurrences sum only exact full-length source-chain instances times their declared copies. Partial/split/overlapping intervals remain separate usages; they are never unioned into an intact functional BindingUnit or a valency. Missing paired-source chains and differing occurrence counts stay visible; no partner or individual-copy contact is generated. The comparison preserves actual saved design/component/source IDs. Missing chains and renamed/deleted endpoints are not silently matched or retargeted. D separates composition and source-numbered substitution tasks while preserving their respective project-scoped drafts and shared molecular selection.

These views establish declarations and data consistency only. Physical assembly, chemical validity, functional valency and experimental performance require independent evidence. Whole-molecule prediction remains unavailable without a validated adapter; imported source maps/coordinates do not acquire broader format scope. Full synthetic J05/current-source regression and independent UI gates passed for the recorded source. Human scientific validation, researcher evaluation and final release gates remain pending.
