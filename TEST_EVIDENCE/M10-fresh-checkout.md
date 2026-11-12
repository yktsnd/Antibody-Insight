# Fresh Windows checkout preflight

2026-11-12 JST · checkout of `344b99e` · P08, J08, AC-J08.

The documented setup passed in a fresh Windows clone created with `core.autocrlf=true`. Python 3.12 created an empty virtual environment, `pip install -r requirements.txt` installed Gemmi 0.7.5, and the browser harness started `start.ps1` on loopback with a temporary SQLite file. Chrome imported the actual 123-residue 3OGO FASTA record, verified the recorded source digest, exported an exact copy of the saved project and recovered it after restarting the launcher. The run recorded zero JavaScript errors and external requests. [Browser harness](M10-fresh-start-browser.cjs)

The exact-source acceptance checker passed in the reviewed worktree and failed in both fresh clones. A byte-by-byte audit of the 112 source files and acceptance artifacts isolated every mismatch to LF versus CRLF.

| Checkout | Source files with mismatched SHA-256 | Acceptance artifacts with mismatched SHA-256 | First checker error |
| --- | ---: | ---: | --- |
| `git clone --local --no-hardlinks -c core.autocrlf=true` | 94 | 8 | Changed acceptance artifact: test_report |
| `git clone --local --no-hardlinks -c core.autocrlf=false` | 12 | 0 | Source changed since acceptance: .gitattributes |

The release evidence needs a stable Git checkout policy for reviewed text and byte preservation for original data and signed reports. Verify the exact same signed source and evidence on both checkout settings after applying that policy. The full release gate remains pending.
