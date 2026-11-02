# F08 local structure observation: independent design review

Design verdict: **PASS**, including the implementation requirements below.
F08 implementation verification and full M2: **NEEDS-EVIDENCE**.
No requester-approval blocker was identified for the proposed explicit-data semantics and known, separately licensed dependencies. This does not approve changing the application license, scientific definitions or external-network default.

Reviewer: `/root/independent_review`, separate from the implementation agent.
Date: 2026-11-03, Asia/Tokyo.
Baseline: `d6d0748897048ce759a4191f1140c05b58e990db` plus ADR-0004, STRUCTURE_CONTRACT, STRUCTURE_RESEARCH_NOTES and THIRD_PARTY_NOTICES as clarified during review.
Traceability: P03/P04/P08 → J03/J04/J08 → AC-J03/AC-J04/AC-J08, F08 only.

## Authorized action and data boundary

E previews/imports local PDB/mmCIF and explicitly supplied correspondence; W identifies antibody/antigen chains, renders actual coordinates and reciprocally selects residues; R exposes original computed evidence and missing confidence. Comparison links orientation/zoom while preserving individual centers and expressly does not claim structural superposition. Original text/digests and immutable IDs/maps must survive restart/export/reimport.

Entities are Structure, StructureMap, Molecule and source-bearing computed Evidence. Measured evidence remains directly owned by Material. A Structure's primary Molecule and antigen's namespaced external target are user declarations, not sequence-based identification or evidence of binding. No prediction, automatic correspondence, numbering, biological assembly or confidence value is generated.

## Identity and provenance review

The clarified residue key retains model, independent author/label chain IDs, segment, independent author/label sequence numbers, insertion code and residue name. Missing source fields stay missing; model identity is not a first-model index. Chain assignments now include segment, avoiding role conflation when an author chain label is reused. Parser-generated entity/subchain/label-sequence assignment and first-conformer helpers are excluded.

Null CIF unknown codes remain distinct from known blank/not-applicable codes. Missing occupancy/B fields must remain null instead of becoming parser defaults. PDB hybrid-36 is explicitly unsupported in this initial adapter; unsupported identifiers must fail visibly rather than become zero. All source atom records must be preserved or the file rejected. Only explicitly supported standard residues may be matched to amino-acid sequence; modified-residue parentage remains unknown.

The following are mandatory implementation details of this design PASS:

1. **One source residue locus maps to at most one sequence position within a map.** Alternate conformers are states of a residue, not separate protein positions. Preserve complete keys including residue name/altloc, but reject assigning alt A to index 1 and alt B to index 2 at the same model/author/label/segment/number/insertion locus. Apply this check to microheterogeneity with different residue names at the same locus as well. A distinct supplied label number still distinguishes genuinely separate source positions. Separate maps may explicitly choose different conformers.
2. **Confidence scope stays explicit.** A Structure may contain several models. A computed metric applies to its declared direct subject and recorded model scope; validate a supplied model reference, or display scope unspecified. Do not repeat a file-level ipTM/pTM as each selected model's confidence. Known model metrics retain kind/unit/range/source/version/time/conditions; zero remains a real supplied value and missing remains null.
3. **Exact source keys precede highlighting.** Resolve chain/model/segment/author/label/insertion/conformer identities and standard-residue consistency before exposing a map. Ambiguous or unavailable coordinates clear/withhold reciprocal highlighting, never fall back to another integer residue or an adjacent atom. Unknown conformer codes remain unmappable; shared blank atoms cannot silently resolve to an unchosen alternate map.
4. **Viewer identity is independent of display parsing.** Stable local renderer atom IDs must map back to the validated complete source keys. Check no dropped/merged atoms and no default model/altloc selection. Viewer-created cartoon/bonds remain display geometry, not recorded chemical/secondary-structure evidence.
5. **View persistence contains only allowed state.** Preserve IDs/residue context and finite camera parameters; store neither atom arrays, sequences nor scores in localStorage. Copy rotation/zoom without copying another structure's center or implying aligned reference frames.

## Primary-source checks

Public sources were opened independently; no private sequence or experimental data was submitted.

- [wwPDB coordinate format](https://www.wwpdb.org/documentation/file-format-content/format33/sect9.html) distinguishes MODEL, chain/residue/insertion fields and alternate locations, including conformers within one residue. It supports explicit source identity and treating alternate locations as alternatives rather than extra sequence positions. Coordinates use Angstroms; B values are source temperature-factor fields, not universal confidence measurements.
- [Gemmi model documentation](https://gemmi.readthedocs.io/en/latest/mol.html) distinguishes author chains, label subchains/label sequence numbers and source segments. Its assignment helpers can generate identifiers or align sequences, and first-conformer iteration can discard alternatives. The current documentation is 0.7.6-dev, so actual pinned 0.7.5 behavior must be verified in implementation tests rather than presumed from the latest documentation.
- [Official EMBL-EBI AlphaFold-Multimer documentation](https://www.ebi.ac.uk/training/online/courses/alphafold/inputs-and-outputs/evaluating-alphafolds-predicted-structures-using-confidence-scores/confidence-scores-in-alphafold-multimer/) supports pTM/ipTM as model confidence metrics with interpretive limits. The application imports those values and assigns no biological pass/fail threshold or measured affinity meaning.
- [3Dmol viewer API](https://3dmol.org/doc/GLViewer.html) provides local rendering/view/click methods; API existence alone is not evidence that reciprocal canvas selection or synchronized camera behavior works. Actual rendered-canvas clicks are required before implementation PASS.

## Dependency and license review

The pinned [Gemmi 0.7.5 license](https://raw.githubusercontent.com/project-gemmi/gemmi/v0.7.5/LICENSE.txt) is MPL-2.0. The proposed unmodified external package boundary preserves its license and source availability separately from application files. Retain upstream notices and the versioned source pointer; packaging or modifying the covered component requires checking those obligations again. No application-license replacement is authorized.

The [3Dmol 2.5.5 manifest](https://raw.githubusercontent.com/3dmol/3Dmol.js/2.5.5/package.json) identifies the pinned version and BSD-3-Clause license. Its [complete tagged license](https://raw.githubusercontent.com/3dmol/3Dmol.js/2.5.5/LICENSE) includes bundled GLmol, Three.js and jQuery notices. THIRD_PARTY_NOTICES explicitly selects GLmol's MIT option and preserves the bundled notices. This is a known open-source dependency adoption within the authorized technical scope, not a substantive relicensing decision.

Read-only local checks verified all three vendor-file SHA-256 values against web/vendor/manifest.json and imported Gemmi **0.7.5** from the isolated ignored environment. The 3Dmol bundle digest is `f7cc78921ae72e7623e89cdd111434f58c2efddd2ffda1cd212644b406fb8016`. This verifies local artifact identity, not parser/rendering correctness or comprehensive dependency security. The implementation review must confirm local serving, retained notices and absence of runtime download/analytics paths.

## Independent edge cases required for replay

1. Two models and two author chains reuse residue number 1, including one insertion and reused labels across segments. Correct scoped mappings work; wrong model/segment/insertion selections cannot highlight the other residue. Missing label IDs/numbers are not copied from author IDs/numbers.
2. A residue has blank common atoms plus A/B alternatives. Explicit conformer choice succeeds; ambiguous choice, assigning the same locus to two sequence positions, and analogous ALA/SER microheterogeneity reject atomically. Clicking a shared common atom must not guess an unselected alternate.
3. CIF `?` versus `.` and absent occupancy/B fields survive distinctly. Negative/zero author residue numbers and known blank PDB chain labels are not confused with missing identifiers or invalid model numbers. Non-finite coordinates reject; literal source B=0 remains zero without a confidence interpretation.
4. Two same-sequence candidates and two structures share the declared antigen reference. Primary Molecule ownership, map IDs and computed evidence subjects remain independent; measured Structure evidence rejects. A multi-model file without a score's model scope displays that scope as unspecified, never supplies each model with the score.
5. Missing/unlisted coordinates, unknown renderer atoms, modified MSE residue and source digest mismatch produce explicit unsupported/unmappable/errors with no wrong reciprocal highlight or partial database write.
6. Actual canvas click → selected source key/sequence position and sequence click → actual atom highlight work after source/model/map switches and restart. Linked orientation/zoom preserve each center and do not create a superposition claim. LocalStorage excludes coordinate arrays/sequences/scores and browser monitoring sees no outbound traffic.
7. Exact limits and preservation: valid boundary-size files, one atom over the limit, malformed files with a late invalid record and old-bundle coexistence. The importer never silently truncates or mutates existing saved source records. Raw text and digest roundtrip exactly as stored.

## Passage boundary

F08 may proceed under these explicit design requirements. Integration requires independent review of actual code, retained regressions, strict source/mapping negatives and physical browser interaction evidence. Full M2 and full J03/J04/J08 are not passed by this design review; hypothesis/design steps, human-validated scientific fixtures and remaining final release criteria stay pending.
