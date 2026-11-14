# M14 independent Workspace residue-to-structure review

**PASS for the exact-source Workspace engineering milestone.** Signed by independent reviewer `/root/residue_structure_review` at 11/14/2026 20:47:02. Scope is the P01/J01/AC-J01 and P02/J02/AC-J02 observation step, with the P03/J03 and P04/J04 controls exercised by the regressions. Frozen implementation commit `2e6d6f8edb9a81a359022aabe07bf6a26520903e`.

## Public structure replay

I started from a detached clone and fresh loopback database, imported the checksummed ordinary paired FASTA and both original mmCIF files through the interface, and explicitly assigned the source chains. The retained deposited-polymer previews reported 432 mapped positions for 1MLC and 427 for 6GC2. At 1440 × 1000, selecting H raw index 47 in either candidate exposed the active residue, exact source label and both complete canvases at once. The active canvas occupied approximately y736–994. The original 698ff76 build required 1,726 px of page scroll to center the canvas. The frozen build required 0 px of page scroll and about 27 px of scroll within the active sequence pane, where the raw 47 button was partly visible before selection. I inspected both rendered screenshots, which show both structures with the active source-residue highlight. [Replayed baseline](independent-baseline.json) · [Independent assertions](independent.json) · [1MLC screenshot](1MLC-selection.png) · [6GC2 screenshot](6GC2-selection.png)

The model-1 deposited keys and displayed atoms were checked against the original atom-site records. The D44.1 selection was TRP, author B:47 / label B:47, 14 atoms with C-alpha at (46.192, 20.883, 59.269) Å. The D44.1des selection was TYR, author H:47 / label B:47, 12 atoms with C-alpha at (−19.892, 101.616, −3.883) Å. The other viewer had no selected atoms when the candidate changed. The inspection produced zero outbound requests or uncaught JavaScript errors and returned a deeply equal persisted bundle before and after residue inspection. [Independent test runner](independent.cjs) · [Input digests](input-digests.json)

## Independent boundary cases

- On 6GC2, changing H to L cleared the prior highlight. L raw index 1 is unobserved in the source, and the view showed unavailable mapping, highlighted no atoms and disabled Focus. L raw 20 resumed mapping to author L:1 / label A:20. L raw 47 selected author L:28 / label A:47 independently of H raw 47.
- Enter selected raw 47, Tab stayed in the sequence at raw 48, and Enter selected its mapped atoms. W → R → W retained molecule, chain and raw position. The jump control crossed the 200-position page boundary and left H raw 201 selected and visible.

## Exact-source regression

I ran the seven existing browser harnesses serially from the same detached checkout. All eight named journeys and all sixteen prescribed negatives passed. The J03/J04 harness also passed its separate public 1MLC structure-scale check. The source manifest records checkout bytes for the acceptance verifier. The named audit binds raw results and confirms exit codes and required case names. [Source manifest](source-manifest.json) · [Named audit](named-audit.json) · [Exit codes](harness-exits.json) · [Public structure-scale regression](public-structure-browser-results.json)

## Product alignment

The researcher can now inspect the deposited position and mutation at the same raw sequence index in the two candidate structures while keeping the candidate and source identifiers available. The established Mol* sequence-above-3D arrangement and Jalview’s linked selection informed a layout that uses the existing viewer and retained correspondence. A separate viewer or alignment system would add work without addressing the recorded page travel. The two structures depict different antigen contexts. The next material gap for the selection decision is the source-lot and offset-bearing time linkage for the original SPR acquisitions. The human assessment of numbering for a design and the unassisted researcher evaluation remain open. [Mol* sequence panel](https://molstar.org/viewer-docs/navigating-by-sequence/) · [Jalview structure tutorial](https://www.jalview.org/tutorial/TheJalviewTutorial_screen.pdf)


