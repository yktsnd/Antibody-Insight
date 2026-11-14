# Antibody Insight — Scientific Design System

**Status:** Proposed product design standard (v0.1)  
**Scope:** Researcher-facing UX/UI, scientific information architecture, interaction patterns, and design review  
**Authority:** Subordinate to `PRODUCT_GOAL.md`, scientific data contracts, and approved acceptance criteria. This document does not change the original eight personas, four primary screens, or scientific semantics.

## 1. Governing principle

> **Design around the scientist's question, not the software's features or data model.**

Antibody Insight exists so antibody researchers can spend less effort locating, reconciling, and transferring fragmented information—and more effort observing molecules, comparing evidence, forming hypotheses, planning experiments, and making scientifically informed decisions.

**A good interface makes the relevant scientific question, evidence, and next action evident through its layout and interaction.** Explanatory prose must not compensate for poor information architecture. Simplicity must never conceal scientific uncertainty or critical experimental conditions.

### Decision hierarchy

1. **Scientific integrity (hard constraint):** identities, provenance, uncertainty, and meanings must remain correct.
2. **Research task completion:** help the user answer the current scientific question.
3. **Information architecture:** present the right information at the right prominence and time.
4. **Familiar scientific interaction:** reuse established, learnable workflows.
5. **Visual implementation:** choose typography, spacing, color, and components to support the above.

If a lower-level design choice violates a higher-level obligation, revise it. Feature quantity, technical sophistication, and visual novelty are not measures of success.

## 2. Seven non-negotiable design principles

| ID | Principle | Required behavior |
| --- | --- | --- |
| DS-01 | **Task-first** | Each screen and major component states the research question it serves and the action it enables. |
| DS-02 | **Scientific truth** | Preserve molecule/chain/residue/material identity, experimental context, provenance, and uncertainty. Never imply unsupported scientific comparability or confidence. |
| DS-03 | **Meaningful hierarchy** | Primary scientific content outranks IDs, configuration, general instructions, and implementation details. |
| DS-04 | **Scientific familiarity** | Prefer proven sequence, structure, and data-analysis interactions over novel generic dashboard patterns. |
| DS-05 | **Context continuity** | Retain and visibly communicate selected candidate, chain, residue, evidence, and decision context across E/W/D/R transitions. |
| DS-06 | **Progressive depth** | Show what the current task requires immediately; make detailed methods and provenance directly discoverable without burying essential caveats. |
| DS-07 | **Minimal invention** | Reuse existing components and conventions. Custom elements need a documented, demonstrable unmet scientific need. |

### Explicit anti-patterns

- Treating every data field as equally important on screen.
- Promoting a local implementation or translation caution to prominent end-user guidance.
- Generic AI-style KPI cards, decorative animations, or invented aggregate scores without research value.
- Long paragraphs placed before the principal molecule, observation, or comparison.
- Designing a new sequence or 3D viewer when existing interaction patterns and components suffice.
- Reducing text at the expense of units, experimental conditions, uncertainty, or the ability to inspect original data.
- Requiring users to rediscover or re-enter the same candidate, chain, residue, or evidence on each screen.

## 3. Scientific information architecture

### 3.1 Context-dependent priority levels

| Priority | What belongs here | Typical placement |
| --- | --- | --- |
| **A — Primary scientific focus** | Current research subject, meaningful comparison/difference, key result, immediate next action | Main workspace and first viewport |
| **B — Supporting scientific evidence** | Linked sequence/structure, measurements, conditions that affect interpretation, uncertainty and comparability status | Adjacent to the focus, synchronized view, concise comparison |
| **C — Detailed provenance and controls** | Original source records, model settings, acquisition details, raw identifiers, hashes, advanced options | Inspectable detail pane, expandable row, source drill-down |
| **D — General and development information** | Introductory help, terminology notes, engineering status, implementation notes | Help, settings, developer docs; unobtrusive status when operationally necessary |

**Priority is contextual, not a permanent classification of fields.** A material lot or acquisition time may be A during assay validation and C during sequence inspection. A caveat that prevents a false scientific conclusion must remain visible even if the underlying provenance is in C.

For every prominent element, answer:

1. Who needs it, for which scientific task or decision?
2. Would hiding or reducing it risk a wrong scientific interpretation?
3. How frequently is it needed in this workflow?
4. Does its location displace something more important?

### 3.2 Visual hierarchy and information density

- Organize information from **scientific subject → meaningful observation/comparison → evidence and limitations → next action → deeper provenance**.
- Encode relatedness with proximity, alignment, shared axes, stable columns, and consistent labels before adding prose or decoration.
- Prefer compact, high-information scientific tables and viewers when they increase scanability; do not equate spaciousness with usability.
- Use typography, spacing, and restrained emphasis to distinguish levels. Reserve prominent alerts for decisions that require attention.
- Put controls next to the data they operate on; distinguish navigation, selection, and data mutation.
- Distinguish **not measured**, **missing**, **not detected**, **below/above a limit**, **zero**, **not comparable**, and **unsupported**. Never invent replacement values.

## 4. Reusable scientific interaction patterns

The reusable unit is not only a visual component: it includes **scientific meaning, state transitions, and source inspection**.

| Pattern | Default behavior | Familiar reference |
| --- | --- | --- |
| **Sequence Viewer** | Continuous residue positions; visible chain and coordinate scheme; numbered positions and region tracks | Jalview, IMGT |
| **Sequence Comparison** | Shared columns **only where a validated mapping exists**; show substitutions, insertions, deletions, absent mappings | Jalview, IMGT |
| **Structure Viewer** | Molecular overview + selected-residue focus; clear chains/antigen; standard rotate/pan/zoom/select; representation choices | Mol*, ChimeraX, 3Dmol.js |
| **Residue Inspector** | Selected residue, numbering/raw/source-coordinate identities, mapping status, neighboring context and direct evidence/design links | Mol* sequence–structure selection |
| **Measurement Comparison** | Candidates in columns, comparable metrics/contexts in rows, units and conditions immediately visible; source drill-down | Scientific data tables |
| **Variant Comparison** | Parent and child identities, exact substitutions, numbering source, provenance and experimental/predicted status | Sequence comparison, mutation tables |
| **Evidence Inspector** | Evidence kind, original subject, observation conditions, source, limitations, and missingness | Scientific laboratory records |
| **Decision Record** | Candidates considered, linked evidence, explicit reasoning, unresolved questions and next experiment | Traceable research decision records |

### 4.1 Sequence-specific rules

- Keep residue positions spatially stable; never use visual wrapping that falsely suggests correspondence.
- Show raw indices, IMGT positions, and deposited-structure coordinates as **different coordinate systems**.
- A shared numbering column may be displayed only for compatible, explicitly selected, scientifically supported numbering maps.
- Show numbering scheme, domain, chain, insertion, and missing mapping where relevant.
- Selecting a residue updates its related structural position and permitted downstream actions without silently changing its identity.

### 4.2 Structure-specific rules

- Default to a scientifically appropriate molecular overview when source data support it; preserve atom-level inspection.
- Reuse the existing local 3Dmol.js viewer before considering a replacement. Evaluate supported cartoon/representation modes and their scientific requirements rather than implementing a new renderer.
- Use consistent chain/antigen identity cues; color is supplementary to text and source IDs.
- Clearly label experimental versus predicted structures, model identity, missing coordinates and selection availability.
- Similar camera orientations are not structural superposition. Different bound/unbound states or experimental contexts must remain visible during comparisons.
- Never synthesize residue correspondences, secondary structures, bonds, or confidence values solely to improve appearance.

### 4.3 Measurements and evidence rules

- Identify **measured**, **literature-reported**, **computed**, **annotated**, **hypothesized**, and **decided** information distinctly.
- Show numeric values with units and indispensable conditions; comparability is explicit, not implied by adjacent columns.
- Literature-reported summaries must not be relabeled as original run-level measurements. Missing run/lot/acquisition records remain missing.
- Preserve the original subject hierarchy (molecule, construct, material, sample/run where modeled). A parent measurement must not become a child's result.
- One direct source-inspection action should be the default for prominent observations; avoid exposing opaque internal IDs as primary labels.

## 5. Four-screen architecture and transitions

Keep the existing E/W/D/R model unless a new design is explicitly approved.

| Screen | Dominant question | Primary visible content | Typical next action |
| --- | --- | --- | --- |
| **E — Candidate Explorer** | Which candidates deserve attention? | Candidate list, meaningful groups and selected comparison criteria | Inspect candidate(s) in W or compare evidence in R |
| **W — Molecule Workspace** | What differs, and where? | Synchronized sequence, numbering/region context, structures, selected residue | Examine evidence in R or consider a change in D |
| **D — Design & Compare** | What is being changed or assembled, and why? | Original/variant comparison, precise changes, lineage and limitations | Record a hypothesis or experiment in R |
| **R — Evidence & Decision** | What do the data support, and what happens next? | Candidate comparison, conditions, uncertainty, reasons, next experiment | Inspect original residue/molecule in W, or save a decision |

### Common screen composition

1. **Compact research context:** project, candidates, active chain/residue/task.
2. **Primary scientific workspace:** the screen's core comparison/viewer occupying most meaningful visual area.
3. **Supporting evidence and next action:** close to the observation they refer to.
4. **On-demand methods, detailed provenance, advanced controls and help.**

Persist important selections through navigation and restore them reliably. On each navigation, make it clear what remained selected and what changed. An unavailable correspondence disables the relevant action with a precise reason; it must not select another residue to make the interaction succeed.

## 6. Visual language and accessibility

### Color

- Use a restrained neutral foundation; color conveys **selection**, **molecular identity**, **difference**, **evidence kind**, **uncertainty**, or **error**, not decoration.
- Keep the same identity colors within a task. Do not silently reuse the same color to mean incompatible things.
- Never rely on color alone: include text, marker, border, legend, or other redundant encoding.
- Use scientific scales appropriate to the measured quantity. Never introduce a red/green good/bad interpretation without explicit scientific justification.

### Typography, spacing, layout

- Favor readable labels and tabular numerals for quantitative values; use a monospaced representation where sequence or coordinate alignment requires it.
- Use a small, consistent set of spacing and text-size tokens; allow compact, task-specific scientific viewers to override general card padding.
- Maintain clear column alignment for comparisons; avoid excessive card fragmentation and empty whitespace between related evidence.
- Make selected and focus states visually distinct from hover and disabled states.
- Support keyboard operation, sensible focus order, zoom, readable contrast, and meaningful labels.

### Internationalization

Use English as the primary implementation/UI language. Japanese researcher-facing text, where provided, must use natural established scientific terminology. A terminology correction is a **local quality rule**, not automatically a new feature or a prominent guide section.

## 7. Design acceptance gates

These are **proposed engineering/UX acceptance checks**, not experimentally validated universal usability thresholds. Preserve higher-level scientific and release criteria.

| Check | Initial acceptance criterion |
| --- | --- |
| **First-viewport comprehension** | At a 1440 × 1000 desktop viewport, the active subject, main observation/comparison and obvious next action are visible without a page-wide search. |
| **Information priority** | Every major UI region has an assigned A–D priority consistent with the current task; critical caveats are not buried. |
| **Selection continuity** | In all eight supported journeys, required candidate/chain/residue/evidence states survive relevant navigation and save/restore operations. |
| **Scientific display integrity** | Zero known critical mismatches between molecular identity, residue coordinates, structure selection and displayed evidence. |
| **Source access** | Each primary measurement/computed result has an obvious, preferably single-action path to its original record or provenance. |
| **Task effort** | Compare click count, page scroll, context switches, re-entry and task time on the *same scientific task* before/after change; set specific reduction targets after baseline measurement. |
| **Reuse decision** | Before a **major new interface**, examine at least two relevant established scientific tool patterns and record the reuse-versus-build rationale. |
| **Human evaluation** | Record task completion, misinterpretations, hesitations and scientific usefulness for each of the eight roles; untested personas remain unverified. |

**Evidence levels must stay separate:** implemented, engineering-tested, scientifically validated, and evaluated by actual researchers. A screenshot, synthetic fixture, or pass count does not establish full scientific usability.

## 8. Design change governance (mandatory)

Before implementing any major UI change, record a short Design Decision Note:

1. **Task:** affected persona, journey, acceptance criterion, scientific question and expected user action.
2. **Information hierarchy:** which elements are A/B/C/D and why.
3. **Reference patterns:** at least two applicable established scientific UX examples, if a major interface is being designed.
4. **Reuse vs. build:** current components and simpler alternatives; why custom behavior, if any, is necessary.
5. **Scientific constraints:** identity, comparability, provenance, unknown values, and security implications.
6. **Acceptance test:** visible result, workflow continuity, error case, and before/after effort measurement.

**Approval required** for changing the product mission, personas, main journeys, underlying scientific meanings, data-provenance requirements, sharing/security model, or approved four-screen architecture. Routine spacing, placement, reuse, and minor interaction decisions may proceed autonomously within these rules.

At each milestone or context compaction, revisit the original mission and ask:

- What can a researcher now **observe, understand, or decide** that they could not before?
- Is the main research action coherent, or have we optimized an isolated component?
- Is the current work more valuable than the largest remaining product gap?
- Could an existing component, simpler layout, or better linkage eliminate the problem?
- Are we elevating incidental implementation details into user-facing priorities?

### Example of an information-priority error

A request for accurate Japanese translation of a technical term is a quality constraint. It does not justify promoting the term's explanation into a high-level introduction or guide. Put the definition beside the specific relevant analysis or in contextual help **only if it aids interpretation**. Generalize this decision rule to all metadata, internal mechanics, and explanatory copy.

## 9. First implementation and validation slice

Do not launch a whole-application redesign or make the design system itself the new product goal.

1. **W:** Improve a real antibody pair's sequence/structure comparison using validated coordinates and familiar representations; measure comprehension, navigation and selection continuity.
2. **R:** Improve observation and evidence comparison so that relevant values, units, comparability and source inspection are visible without competing administrative metadata.
3. **W → D/R:** Validate one complete observation → evidence → proposed action → saved rationale journey using real public antibody sources, without fabricating missing sample provenance.
4. **Scale:** Reuse patterns that survive independent scientific and researcher review in E and D, then in all eight journeys.

A milestone is accepted only if the revised interface measurably helps the specified researcher task **without reducing scientific correctness, source transparency, or data integrity**. Passing this slice is not completion of the entire product.

## 10. Reference conventions

These are design references, not blanket permissions to copy source code or assets. Verify current licenses and integration constraints before embedding components.

- [Jalview documentation](https://www.jalview.org/help/html/) — sequence alignment, residue selection, feature tracks and annotations.
- [Mol* viewer documentation](https://molstar.org/viewer-docs/) — molecular display and sequence–structure interaction.
- [3Dmol.js documentation](https://3dmol.org/doc/) — reusable local molecular representation and viewer operations.
- [IMGT numbering](https://www.imgt.org/IMGTScientificChart/Numbering/IMGTnumbering.html) — antibody numbering and region semantics.
- [Nielsen Norman Group: usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) — consistency, recognition, feedback and reduced cognitive burden.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) — perceivability and accessible interaction, including not using color alone.

---

**North-star acceptance question:** *Can an antibody scientist start from a meaningful molecular observation, inspect the right evidence with minimal friction, and confidently explain the next research action—without having to reconstruct relationships across disconnected tools?*