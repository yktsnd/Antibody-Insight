# F06 implementation and M1 foundation: independent review

F06 implementation: **PASS**.
DEVELOPMENT_PLAN chapter 9 M1 foundation passage gate: **PASS**, limited to its engineering identity/lineage, persistence and safe-rejection requirements.
Complete J01–J08, scientific golden-fixture validation and Release 1.0: **NEEDS-EVIDENCE**.

Reviewer: `/root/independent_review`, separate from the implementation agent.
Review date: 2026-11-02, Asia/Tokyo.
Repository baseline: `ab6f4d6f22fe73396b1cb455fecc63b74239c8fd`, plus the reviewed F06 working-tree changes.
Final reviewed source set: TEST_EVIDENCE/M1-F06-independent-source-manifest.json, digest `925f8cb7e947093d9ccc05785bc0665db12a1cba631896eb48d2cae713fe20a4`.

## Scope and authority

P02/P05/P08 → J02/J05/J08 → AC-J02/AC-J05/AC-J08, F06. Previous F01–F05 invariants and user actions were retained and replayed.
The reviewer read workspace_app/composition.py, domain/fixtures/server changes, web/app.js composition/history rendering, tests/test_composition.py and the extended tests/browser.cjs against the approved ADR-0002 and COMPONENT_CONTRACT.
The reviewer added tests/test_composition_independent.py and evidence files only, and did not edit product code.

User action: E previews and saves locally declared units/molecular graphs/history; W exposes ordered components, copies, exact origins and immutable before/after lineage; export/restart/reimport preserve the saved identities and content.
The implementation validates declared metadata consistency. It does not validate binding, folding, pairing, chemistry, actual copy-specific contacts or predicted applicability. It does not infer molecular format, numbering, structure correspondences or scientific scores.

## Independently executed evidence

- `python -m pytest -q`: **104 passed in 11.30s**, exit 0, including 13 new independent F06 cases and all previously retained tests.
- Real Chrome replay of `node tests/browser.cjs` with the existing documented NODE_PATH: **11 checks PASS**, exit 0, Chrome `156.0.8078.79`.
- Browser report: TEST_EVIDENCE/M1-browser-results.json, final independent run `2026-11-02T14:51:08.365Z`, initial exported-dataset digest `797f4ca3cfd633a85391485d23974ec2ad231fe162f9475d6465620db9f7642d`.
- `python scripts/check_traceability.py`: **PASS**, eight future journey definitions and six implementation slices. It correctly reports **0/8** complete journey executions and **0/16** prescribed final browser negatives; foundation checks are not counted as completed final journeys.
- TEST_EVIDENCE/M1-composition-screen.png was visually inspected. Component order/copies, declaration limits, raw sequence indexes, lineage, absence of child construct/material and retained selection are visible. Scientific/data integrity was established through assertions and stored-data comparisons, not the screenshot alone.

Observed command output is retained in TEST_EVIDENCE/M1-composition-independent-test-log.txt.

After the execution, the implementation agent changed the displayed version to `0.2.0-dev` and clarified D's explanatory text that stored composition/history can already be inspected in W while interactive creation remains future work. The reviewer inspected both changes; they do not alter validation or operation behavior. The final source manifest includes those text/version changes. The full suite was not repeated solely for those wording changes.

## M1 passage gate replay

| Chapter 9 requirement | Verdict | Evidence |
|---|---|---|
| ID/lineage fixed checks all pass | PASS | Typed independent BindingUnit/Molecule/Construct/Material IDs; exact scoped origins; ordered components/copies/connections; immutable exact parent/child signatures; separate iterative provenance/lineage DAG validation; all current fixed engineering tests pass |
| Save and reload | PASS | SQLite close/reopen and full equality tests; actual browser server restart; JSON into a new database preserves metadata and identities; graph-free records remain graph-free |
| Safely reject anomalous data | PASS | Atomic unknown fields/types, malformed/wrong/cross-project references, invalid intervals/copies/endpoints, sequence mismatch, duplicate connections/lineage, cycles and signature tampering; existing data remain unchanged |
| No erroneous joins or silent overwrites | PASS | Equal-sequence units retain exact source identities; global ID collisions reject; parent measured Evidence remains on original Material; lineage creates no child measurement |
| Independent implementation verification | PASS | Separate reviewer inspected source, proposed new cases and independently reran domain/HTTP/browser checks |

The plan's final 18 human-validated scientific golden fixtures are still unavailable and unverified. This M1 engineering gate PASS does not certify those fixtures, numbering/CDR correctness, biological assembly correctness or researcher acceptance. Those requirements remain open, and no final-release gate is waived.

## Independent edge cases and findings

The 13 added cases cover:

1. Initial and composition fixture projects coexist in the same database with disjoint internal entity IDs.
2. A component ID present on another chain cannot satisfy a wrongly scoped endpoint.
3. A real existing Molecule from another project cannot satisfy a BindingUnit origin; the pre-existing project remains unchanged.
4. Four interval cases reject zero, boolean and floating-point indexes without coercion.
5. An exact last-residue origin and the declared maximum 100 copies survive restart.
6. A lineage snapshot changing an origin to another same-sequence unit is rejected; sequence equality cannot replace source identity.
7. A **1,100-level** provenance chain combined with a valid opposite-direction parent→child lineage DAG imports with reversed input order and survives reload without recursion failure.
8. A late cycle in that long provenance graph rejects the entire batch.
9. Unknown fields on each new entity type reject atomically with field-path evidence.

One concrete issue was found and corrected before this verdict: composition_bundle initially reassigned Project IDs while reusing the first fixture's entity UUIDs, making the two provided fixture projects conflict in a single workspace. The implementation now deterministically namespaces composition fixture entities and references. Both the independent coexistence test and actual browser flow importing composition alongside the original fixture pass. Rejection had prevented data corruption; the fix restores the intended fixture demonstration path.

No additional unresolved P0/P1 issue was found in the reviewed foundation implementation.

## Scientific meaning, compatibility and security

BindingUnit topology and intercomponent connections remain explicit declarations with source metadata. Copies and interval indexes are strict bounded integers. Every named source interval reproduces the declared sequence and stays tied to its exact typed, project-scoped origin. Unknown fields and unsupported kinds fail visibly. Reversed same-kind connection duplicates are rejected while different declared kinds remain distinct.

Before/after signatures use type-aware exact JSON comparisons. Absent graphs appear as null only in signatures; existing molecules are never rewritten to add them. Lineage and provenance checks use separate DAGs, so a legitimate child deriving components from a parent is not accidentally rejected because lineage points parent→child. Append-only SQL storage and transaction boundaries remain intact.

The composition UI escapes source text and presents the limits of declaration-only validation and undefined copy-specific contacts. The unchanged local request controls remain active; the complete browser replay records no external requests or JavaScript errors. This remains a local development security result, not a shared-user security certification or a comprehensive ASVS audit.

## Remaining work

Full J02/J05/J08 are still incomplete: numbered editing, interactive assembly/comparison, validated structures/numbering, complete file adapters and final decision workflows remain later work. The other five complete researcher journeys also remain pending. Human-validated scientific fixtures, researcher evaluation, final coverage/performance/storage/security criteria and final independent eight-journey replay remain required.

F06 may integrate with its traceability and exact tested revision recorded. Subsequent domain changes require another independent review. Documentation should distinguish stored declared composition/history, which is now implemented, from interactive design and scientific validation, which remain pending.
