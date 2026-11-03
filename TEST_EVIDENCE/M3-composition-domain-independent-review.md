# F14/F15 composition domain/API: independent review

Verdict: **PASS for the reviewed domain/API slice.** UI integration, complete J05 and M3 remain **NEEDS-EVIDENCE**.

Reviewer: `/root/observation_review`. Date: 2026-11-03, Asia/Tokyo. Trace: F14/F15, P05, J05, AC-J05. Reviewed `workspace_app/assembly.py`, the composition API branches in `server.py`, existing domain/graph/storage contracts, ADR-0008 and the independent design constraints. No product source was edited by this reviewer. This is not a complete-J05 or new whole-working-tree acceptance registration.

## Scientific and identity assessment

Recipe source parts resolve an actual same-project BindingUnit, its named chain and exact inclusive integer interval. Independent components require actual sequence and role. Existing graph validation checks chain/copy/part consistency, exact sequence concatenation and declared endpoints; no pairing, missing component or format is inferred. The summed chain-length limit is enforced before concatenation rather than clipping output.

`composition_context` preserves each actual source-chain usage, component instance, interval and declared copies. Its `full_source_chain_occurrences` counts only full source-chain instances multiplied by declared chain copies; split/overlapping partial intervals do not become a complete occurrence. It does not count functional units or infer valency. Absent paired chains stay absent; different paired copy totals remain independently visible. The UI must retain those meanings and show their limitations.

A new independent design has no invented parent or Lineage. An explicitly chosen parent requires a reason and exact differing composition signatures. Optional researcher notes remain local-entry annotation Evidence with null numeric value, not experiments or predictions. Original Molecule/Construct/Material/Evidence/maps/structures stay unchanged; nothing is inherited as a new measurement. Connection cycles remain declarations under existing endpoint validation, separate from provenance/Lineage DAG requirements.

## Independent tests and actual HTTP verification

Added six tests in `tests/test_assembly_independent.py`. Executed:

`.venv/Scripts/python.exe -m pytest -q tests/test_assembly.py tests/test_assembly_independent.py --tb=short`

Result: **31 passed**, exit0, in4.97 seconds. Evidence: `M3-composition-domain-independent-run.log`. Tests use synthetic fixtures, temporary SQLite databases and loopback servers; no user research database or external service is involved.

Independently proposed boundaries exercised:

- Repeated full/partial/overlapping/split source instances and a distinct equal-sequence unit retain exact IDs/intervals. Paired source copies2 versus1 remain separate; union coverage creates no extra full occurrence. Returned context mutation cannot rewrite stored input.
- A chain of exactly100000 residues is preserved; appending one residue rejects the summed length without clipping, changing input or inventing a sequence.
- Reordering connected components preserves their IDs/endpoints even with equal sequences. Deleting the referenced part rejects instead of retargeting another part.
- Real authenticated HTTP preview is read-only. Missing session, wrong CSRF and foreign Origin are rejected. Attempting to promote the new annotation into a measured Molecule result rejects the entire import; the valid preview saves atomically, duplicate save rejects, and authenticated context resolves the exact saved source.
- A source ID existing elsewhere in the database cannot cross the request's project boundary. Extra envelope/definition/source fields cannot spoof provenance or substitute supplied sequence for the authoritative source interval; both original projects remain unchanged.

The retained25 tests also cover explicit parent/no-change rejection, malformed/undefined recipe data, exact source roundtrip, absent paired source, permitted declared connection cycle and undefined composition without autofill. No domain/API defect requiring a product-code change was found in this review.

## Remaining gates

Domain identity/provenance and the tested local API safeguards: **PASS within this slice**. The implementation agent may proceed with the approved interface. This does not certify recipe UI ownership, unsupported-analysis presentation, complete comparison, real keyboard/mouse research flow or all regressions on the changed source.

Require independent full J05 E→D→W→D→R plus actual restart/export/reimport, both prescribed negatives, newer-draft/project race checks and fresh retained J01–J04 source-bound regression before integration. Earlier accepted4/8 journeys and8/16 negatives remain historical engineering evidence; this domain review adds none. Scientific goldens, researcher evaluation and final release gates remain open.
