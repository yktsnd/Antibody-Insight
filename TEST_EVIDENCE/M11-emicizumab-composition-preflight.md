# Public bispecific composition preflight

2026-11-13 JST · P05/P08 · J05/J08 · AC-J05/AC-J08.

The public NIH GSRS entry for emicizumab version 37 contains distinct Q and J heavy chains and separately numbered L1 and L2 light chains with identical amino-acid sequences. The FDA quality review confirms the chain roles and lengths. The original registry's residue-level disulfide references provide a direct check on the reported chain pairs. [GSRS record](https://gsrs.ncats.nih.gov/api/v1/substances(7NL2E3F6K3)) · [FDA quality review](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2017/761083Orig1s000ChemR.pdf)

The preflight extracted four FASTA records, registered all four source chain IDs, declared two binding-unit source pairs, and saved a composition through the existing preview and store. The saved L1 and L2 were distinct, each with one copy and its own source interval. Each linked component pair agreed with the registry. Reopening the database and restoring the exported bundle into a fresh store produced equal records. Deleting L2 from the submitted recipe while keeping its declared connection was rejected without changing the store. [Replay](M11-emicizumab-composition-probe.py) · [Results](M11-emicizumab-composition-probe.json)

The four source interchain disulfides correspond to three component pairs. Q and J have two distinct residue-level bonds in the registry. The current composition contract stores one declaration between their components and does not retain the residue endpoints or number of bonds. Retain the registry record for those details. This preflight verifies application behavior against one public input. J05's interactive comparison of an alternate design, independent human scientific review and researcher evaluation remain pending. [Review expectations](../validation/emicizumab-reference-expectations.json)

Run from the repository root with the normal Python dependencies.

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe TEST_EVIDENCE/M11-emicizumab-composition-probe.py
```
