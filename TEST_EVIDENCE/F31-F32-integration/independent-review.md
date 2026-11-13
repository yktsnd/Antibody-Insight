# Independent import and checkout review

**PASS.** Signed by independent reviewer `/root/import_review` at 2026-11-13T00:03:01.454298+00:00. Scope covers P08 / J08 / AC-J08 on frozen implementation commit `cd3a6d70ca7a999e8279187edfcae9fe3bfdd108`, the checkout portability change at `fac126e50f4d93025ff068035111aa579a24cda7`, and the named J01–J08 engineering regression replay.

## Reproduction and provenance

In an independent Windows Chrome replay, the researcher imported local FASTA, PDB, measured CSV and canonical/native computed JSON, registered Construct and Material, and inspected explicit coordinate correspondence, model scope and unsupported paths. A process restart and export/reimport into a fresh SQLite store retained IDs, evidence types, provenance timestamps and subjects, correspondence, hypotheses, lineage, both Decision revisions and original structure/prediction bytes. Duplicate-ID collision and damaged coordinate input left existing records intact. The named import-race regression preserved the selected file after a project/title change and let pasted text take precedence. The replay blocked non-loopback requests and reported zero outbound requests and JavaScript errors. [J08 browser results](TEST_EVIDENCE/M5-J08-browser-results.json)

## Independent import edge cases

- Closing the dialog while a read and preview were pending, then reopening with a second delayed file, discarded the first preview. Only the reopened filename and record reached the preview request.
- Explicitly switching from unpaired FASTA to grouped FASTA while a read was pending preserved the user-selected format and title. The grouped preview received both records and their original CRLF text.
- Replacing a pending malformed UTF-8 file with a valid FASTA left the valid preview and status unchanged after the old decode failed. All three cases canceled without a stored change. The browser reported zero outbound requests and JavaScript errors. [Independent results](independent-j08-edge-results.json) · [Independent harness](independent-j08-edge.cjs)

## Regression and portability

Fresh independent Windows checkouts at the same commit with effective `core.autocrlf=true` and `core.autocrlf=false` produced the same 112-file SHA-256 manifest `a8401ea90d8df073cc3c831af20a8949c9407958beb863475d017f96275890b9`. All 17 prior F30 acceptance artifacts and the original NIST FASTA matched their committed bytes in both. The traceability CSV had equivalent parsed content with checkout-specific line endings. Chrome passed all eight named main cases and all sixteen prescribed negatives. The separate Python regression run passed 564 tests. [Source manifest](source-manifest.json) · [Checkout results](portability-results.json) · [Named audit](named-audit.json)

## Product alignment

P08 asks whether another researcher can recover the exact data and reasoning behind a decision. The replay moved from the actual import, residue and evidence screens to a fresh project with matching retained records. The fix preserves file ownership during the existing preview; it requires no additional user step or import route. The original Traceability acceptance references a previous reviewed source manifest and needs the evidence links refreshed to match the reviewed bytes. The largest remaining product gap is observing the full workflow with human-verified numbering and original assay evidence tied to a real material and acquisition event, then evaluating it with researchers. The named PASS is engineering acceptance with labeled synthetic inputs. The 1MLC replay verifies public-source viewing and scale. Scientific validity, researcher evaluation and final Release 1.0 acceptance remain open.
