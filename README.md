# Antibody Insight

Inspect candidate sequences, local coordinates and quantitative observations together in a Windows desktop workspace.

## Start

Extract `AntibodyInsight-Windows-x64.zip` to a folder and open `AntibodyInsight/AntibodyInsight.exe`. Local builds also place the executable in `dist/AntibodyInsight/`. The Windows build uses the installed Microsoft Edge WebView2 runtime. Keep all files in the folder together.

To run from source with Python 3.12 on Windows, open PowerShell in this directory.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\start.ps1
```

## Inspect a project

1. Choose **Open example** and choose an unused filename. The short sequences, coordinates and observations are synthetic. **New** creates an empty project. **Open** resumes a saved `.ais` file.
2. Expand a candidate in **Antibodies** and select a component. The sequence, structure and plot highlight follow that selection. Click a point in **Plots** to inspect its component or candidate. For a candidate-level measured point the workspace keeps its current component or opens its first component. Hover over the point to see the sample.
3. Select a sequence position or click an atom in a mapped structure. The structure header gives the source chain, residue number and insertion code. Choose a component of the same alphabet under **Compare** to view the original record positions side by side. Choose **Align sequences** for a global pairwise alignment. Identity counts identical letters among columns that contain two letters. Gap columns are counted separately. The display reports its scoring parameters. At a uniquely aligned residue, **Inspect aligned reference** opens the reference at its own position. Gaps and tied optimal alignments have no cross-record navigation.
4. Choose **Export FASTA** to write the selected component. Its stable ID, candidate key, component label and alphabet accompany its registered sequence. **Project note** stores one free-text note in the project.

Choose **Whole record** for an overview of a long sequence. Each bar occupies its recorded interval. Choose a bar to inspect its position, or set **Position** directly. Drag **Zoom** to follow the selected coordinate from the full record down to a single letter. In a translated region, the coding track gives all three source bases, including bases in different exons. The project remembers the zoom for each component.

## Import local research data

Use **Import → Choose file**, review the assignments and choose **Save reviewed records**. Each table import commits as one transaction. Source bytes, filename, fingerprint and import time stay in the project.

- **Sequences**. Use [the sequence template](examples/sequences.csv) as CSV, TSV or a single-sheet Excel workbook. Candidate keys group components within one project. Assign distinct component labels within a candidate. For FASTA, choose the DNA or protein alphabet explicitly and check the candidate and component fields in preview.
- **Annotated DNA**. Open SnapGene `.dna` or GenBank records. Inspect **Annotations** for strand, intervals and available CDS translations. A deposited segment can have a verified translation without a terminal stop. An explicit `mat_peptide` with a unique parent CDS and codon-aligned boundaries enables mature-chain navigation. A known start with an open end is shown as a fragment. Complete mature FASTA export requires two exact boundaries. A signal peptide alone does not establish the mature sequence.
- **CDS coordinates**. In the example, select **Example A → Example plasmid** and choose DNA base 8. The coding strand reads GCT across source bases 9, 8 and 4. **Inspect Peptide** opens the matching registered protein at Ala 2 and highlights structure residue A 10A. **Go to source codon** returns to base 9. The terminal stop has no protein residue. A link requires an explicit choice, exact translation identity and the same candidate.
- **Mature chain**. Select **Example A → Annotated precursor**, then base 10. The display identifies precursor residue 4 and mature residue 2. **Inspect Peptide · mature 2** opens the registered mature chain. **Export mature FASTA** writes the annotated mature sequence with its source fingerprint and precursor interval.
- **Observations**. Use [the observations template](examples/observations.csv). Match the exact project candidate key and supply the actual sample key for measurements. Keep different units, sources and conditions explicit. Blank numeric cells remain missing. Accepted kinds are `Measured`, `Computed`, `Reference measured` and `Reference computed`. A supplied event time includes its UTC offset. The graph plots individual records.
- **Repeated measurements**. Open the example and import [the measurement series](examples/measurement-series.csv). Choose **Demo signal** in **Plots**. Example A has three numeric readings and one blank. Its mean and sample SD are both 2 AU. Example B supplies only a mean and SEM. Switch between **Mean ± SD**, **Mean ± SEM** and **Individual readings**. **Source records** shows the readings or reported summaries for the selected candidate. Calculations require an explicit replicate set and matching candidate, metric, kind, unit, conditions and source. An empty count or error stays unknown. To enter a record directly or paste a table including its headings, choose **Import → Enter or paste measurements** and review it before saving.
- **Coordinates**. Select the intended component, choose **PDB / mmCIF** and confirm the source chain. A matching deposited mmCIF polymer can include unobserved positions. The viewer maps each supported observed position to its author chain, number and insertion code. Selecting a missing position displays its status. Coordinates with a different sequence or ambiguous chain correspondence can be viewed without a sequence link. Support is limited to single models representable in the local PDB display format. The original file is retained.

Keep the project on a local drive. Close the application before copying its `.ais` file for backup. Install dependencies before working offline. Project data and the viewer assets are local.

## Compare two metrics

In the example, import the measurement series above. In **Plots**, choose **Demo signal** for the vertical axis and **Example recovery** for the horizontal axis. Each point represents one candidate. Both axes use the displayed unit, origin, conditions and source. A candidate contributes when each axis has one numeric mean or one ungrouped numeric record. **Source records** shows which candidates have missing or ambiguous values. The displayed Pearson correlation uses the included pairs and is undefined for constant axes or fewer than two pairs.

Click a point to inspect its candidate. **Save plot PNG** writes a 1,920 × 1,200 image with axis context and the selection. **Export comparison** saves an Excel workbook with the correlation, candidate values, exclusions and imported source records, including sample IDs, event times, filenames and SHA-256 fingerprints.

## Compare variable domains

Open a registered protein and choose **Antibody domains**. The app numbers antibody variable domains locally using Immunum. Switch between **IMGT** and **Kabat** while tracking the same original residue. Use **Go to region** to jump to the first supported residue of a CDR or framework. The orange selection and author residue in a linked structure follow the original sequence position.

Add a domain to the comparison, then select another registered protein and add its domain. The matrix aligns domains of the same chain type within one numbering scheme. Select any residue to open its candidate at that position. Dashes indicate no residue at that label. The frequency row reports occupancy among the selected domains and shows observed residue counts when you hover. Domains lacking terminal numbering or key anchors can be inspected, and the comparison includes domains with supported coverage and anchors.

## Compare declared regions

Choose **Compare regions** in **Sequences**. For each candidate, select a registered component and add an exact source annotation or an inclusive range. The first region anchors the comparison. A joined reverse-strand annotation is shown in its recorded direction. Selecting a letter opens its original sequence position. For coding DNA, use the coding track to follow the corresponding translated residue.

The identity matrix reports matching known letters over paired known letters at reference positions. Unanchored insertions have their own columns and are excluded from cross-region identity. Tied alignments show their provisional letters with an ambiguous status and no cross-region identity. **Export comparison** saves the alignment letters, gaps, source positions and hashes, plus the identity counts, to an Excel workbook.

## Compare structures

Select a coordinate file and pick a second mapped chain under **Overlay structure**. **Side by side** keeps both cameras synchronized. Enter two positions in **Fit range** to fit a region of the displayed sequence, or leave both blank to fit all paired positions. The fit uses shared observed Cα atoms with positive occupancy and a single location. The display reports the RMSD in ångströms, the number of contributing pairs, and the selected author residue on each chain. **Focus residue** centers the selected residue. **Save structure PNG** writes the current view with the file, selection and fit context.

To attach externally calculated values, select their coordinate file, import a sheet matching the [structure values template](examples/structure-values.csv), and confirm the coordinate file and chain in preview. **Structure values** shows the selected model’s values. Choose **Use for candidate metrics** to make those values available in **Antibodies** and **Plots**. Choosing or comparing other display models leaves that assignment in place.

Use **Bookmarks** to name and restore an observation, including the selected residue, comparison, plots and camera. Restoring a bookmark keeps the current project note and representative structure.

## Build and verify

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\build.ps1
```

The implementation covers the workflows described above. See [development and acceptance records](DEVELOPMENT.md) for the verification scope.
