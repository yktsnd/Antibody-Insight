# Numbered design and hypothesis contract

F10/F11 implement the original M3 parent/reference → design → retained reasoning path.
Related authority: PRODUCT_GOAL, DEVELOPMENT_PLAN J02/J03/J04/J06 and AGENTS.

## Exact substitutions

A request names a parent molecule, child name/external ID, reason and nonempty substitutions.
Each substitution names an imported parent map, integer number, insertion code, target amino acid and optional reference map.
The server resolves the named map's actual molecule/chain/domain/coordinate/raw index; it does not trust a client-supplied raw offset or infer a missing map.
Only mapped, eligible source-verified or explicitly synthetic engineering maps may authorize a design position. Each requested position must exist; a partial map authorizes only its actual observed positions.
Targets are the 20 canonical amino acids; other targets report unsupported rather than silently substituting another symbol. Repeated source positions, unchanged replacements, malformed coordinates and empty designs reject.

The immutable substitution Lineage records complete before/after composition signatures and every actual mutation's map/chain/domain/scheme/number/insertion/raw index/from/to identity. Optional reference map identities remain traceable, with unavailable reference positions explicit. Any imported fabricated change set rejects unless it exactly reconstructs the child from the named parent.

The parent is unchanged. The child has a new ID/source and new sequences; it acquires no measurements, constructs, materials, structures or verified maps by inheritance. D displays changed regions from the parent map with that scope made explicit. Child numbering remains unverified/unregistered until separately supplied; no derived attestation is created.

For a component graph, unchanged components/connections/copy counts are preserved. Touched component sequences are updated to exactly match their chain. Changed components lose their now-invalid exact BindingUnit interval and explicitly display origin unavailable on the child; parent graph/Lineage retains the source. The preview shows every such change and all affected declared copies. This is a sequence design, not a claim about pairing, chemistry, assembly or binding.

## Hypotheses

Hypothesis is an immutable typed entity with status `proposed`; it is never an Evidence record or scientific fact.
It contains text, question/next experiment, optional recorded limitations, molecule IDs, related Evidence IDs, lineage IDs and explicit residue/structure references.
All references resolve within the same project. Related evidence remains on its original subject; its molecule must be among the explicitly related molecules. Lineage parent and child must also be included in the hypothesis's molecule set.
Residue references name actual molecule/chain/raw index; any numbered design is reached through its Lineage/map identity. Structural references name the actual source, model and optional correspondence; unknown source model remains null, never invented as model1.
The source records the actual local researcher-entry mechanism/application version, not an authenticated identity. No score, evidence, confidence or validation status is generated from hypothesis text.

F12 optionally retains an actual structural `residue` within each structure reference: `{source_key, altloc}`. The source key contains exactly the eight preserved residue fields in STRUCTURE_CONTRACT.md. Typed exact equality, the actual file/model and supplied alternate state are validated; no adjacent, same-number or same-sequence fallback is allowed. Source-only antigen/other context can be saved without any antibody sequence reference or measurement attribution. Legacy references without this optional field are preserved unchanged. Full source keys are resolved locally in memory for hypothesis review, not copied to localStorage.

Evidence may optionally carry `description` (source-supplied qualitative text or null) and `residue_refs` (up to1000 unique chain/raw-index pairs). These associations resolve only through that Evidence's actual subject path to its own molecule. A measured Evidence still directly targets Material and retains the original scalar, units and conditions. “Source-reported position” does not imply residue-localized measurement, causality, liability classification or prediction from note text. Missing scalar data stays null. Legacy Evidence without either optional field is preserved without adding defaults.

D/R preview the exact targets, proposed text, next test, limitations and linked source IDs before an explicit atomic save. A hypothesis can target an existing candidate without generating a child (J03), or a parent/child pair with a saved design (J02/J04). R lists hypotheses separately from measured/computed/literature/annotation evidence and shortlist drafts. Restart/export/reimport must retain exact text, IDs and source contexts.

## Engineering acceptance

Required main path: real browser operations for the full J02 action, with VH/VL, an explicitly supplied reference, exact insertions, saved child/lineage/hypothesis, actual restart and exact data comparison.
Required negative paths use the original names `e2e_j02_numbering_unavailable` and `e2e_j02_insertion_mapping`.
Keep the existing J01 and structural paths intact. J03/J04 need their own complete evidence before being counted; engineering fixtures never satisfy human scientific golden validation or researcher evaluation.

Design review PASS: TEST_EVIDENCE/M3-design-independent-review.md. F10/F11 and the full synthetic J02 path passed independent review in TEST_EVIDENCE/M3-numbered-design-independent-review.md. That F10/F11 registration covered J01/J02. The subsequent F12/F13 review in TEST_EVIDENCE/M3-observation-implementation-independent-review.md independently verifies full synthetic J01–J04. Full M3/J05–J08 and scientific/user validation remain pending. UX references and reuse decisions: SCIENTIFIC_UX.md.
