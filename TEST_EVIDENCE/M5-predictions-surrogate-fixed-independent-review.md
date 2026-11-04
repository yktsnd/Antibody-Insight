# Independent malformed-Unicode HTTP fix review

Verdict: **PASS for the bounded error-response serialization fix.** Reviewer: `/root/prediction_design_review`, separate from implementation. Date: 2026-11-05, Asia/Tokyo. Trace: F21/F22 / P08 / J08 / AC-J08, safe rejection of bad input with preserved existing data. No product code or tests were edited by this reviewer during fix verification; only separate probe/evidence files were added.

Reviewed server.py SHA-256 `1cdb3175ea28c680239c733255ff94aeb23029b224a27e4df602e76e92a277d3`, identical before and after replay. The change selects ensure_ascii=True for error HTTP statuses. Successful responses and the authoritative serialized_bundle retain their prior exact serialization. The imported raw file, digest, selected subjects/models, scalar types and scientific interpretation are unaffected. No new user decision or scientific assumption is introduced.

The independently preserved original ten-case probe was copied to `M5-predictions-surrogate-fixed-independent-probe.py`, changing only its two result filenames so it cannot overwrite original failure evidence. Command:

```powershell
& ./.venv/Scripts/python.exe TEST_EVIDENCE/M5-predictions-surrogate-fixed-independent-probe.py
```

Result: **10/10 expected outcomes**. Lone high/low surrogate unknown root keys and duplicate root keys now return complete422 JSON instead of closing the connection. Known-row surrogate subject/metric/description/context-key/context-value cases also return422. The valid paired-Unicode control returns200 on the same authenticated session. The database remains unchanged in10/10 cases. The new server-errors log is empty, with no uncaught traceback.

Evidence: `M5-predictions-surrogate-fixed-independent-results.json` (SHA-256 `f5feeeaa8774f98260dcc3468532a0e61bfe005bc7bad1493c7241ebfe471607`), `M5-predictions-surrogate-fixed-independent-replay.log` and `M5-predictions-surrogate-fixed-independent-server-errors.log`. Original failure results retain SHA-256 `7ff955d3aaa1a2fe27ea0aebdd625b00942ec38dad2decfce8c0f2e64f09279c`.

Also independently ran:

```powershell
& ./.venv/Scripts/python.exe -m pytest tests/test_predictions.py tests/test_predictions_independent.py tests/test_predictions_dto_independent.py -q --tb=short
```

Result: **86 passed in10.37s**, including the implementation's four new HTTP regressions, earlier source/allocation/identity cases and independent DTO typed-value checks. Log: `M5-predictions-surrogate-fixed-independent-tests.log`. Current implementation test file SHA-256: `aa990a5d9d3266c7e6275d0116af1aa6a6ccf6c6ee88226a4c012e654d6f23c1`. Predictions.py remains `37f2b0f545c484b272a92e6385b2f5694b5916c343d4e104127e6d7e3c5037db`.

The repair resolves the independently observed connection-close defect without reducing the original research action. Reliable rejection lets P08 correct an input and continue inspecting/reproducing the actual registered project. The original FAIL remains documented separately; this is its bounded closure. Earlier domain/DTO approvals retain their separate scope. Full browser J08, all-journey final frozen regression, human scientific/user validation and final release gates remain pending. This report does not claim all eight flows or product completion.
