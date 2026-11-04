# M5 native parameter JSON transport: independent addendum

Verdict: **PASS for this bounded domain/API delta.** Native preview may receive computation conditions as literal JSON text, parse that text once with the existing strict parser and store the resulting object/null. Persisted prediction_file options and direct awx import retain the existing object/null contract. No scientific scope, identity, provenance meaning or external-network policy changes. Browser operation, full J08 and final integrated acceptance remain pending.

Reviewer: `/root/prediction_design_review`, separate from implementation. Date: 2026-11-04, Asia/Tokyo. Trace remains F21/F22 / P03,P08 / J03,J08 / AC-J03,AC-J08. This supplements the original domain/API report without changing its bytes or hashes. Only new independent tests/evidence were written by this reviewer.

Reviewed predictions.py SHA-256 `37f2b0f545c484b272a92e6385b2f5694b5916c343d4e104127e6d7e3c5037db`, identical before and after this replay. The change deep-copies the caller's options and decodes conditions only when the adapter is native, the options are an object and conditions is a string. Existing strict shape validation follows decoding. The earlier reviewed domain.py, adapters.py, storage.py and structures.py hashes remain unchanged. server.py additionally serves the new predictions.js static route; its current hash is recorded in `M5-predictions-domain-dto-independent-source.json`. This static exposure does not change the reviewed API validation; it is not a browser approval.

Independent test source: `tests/test_predictions_dto_independent.py`, SHA-256 `7ae637448baaa201800f92b70fc6e74d989f6e3a937eaddb1fe26ea65411d3b5`. Fourteen new cases test:

- Literal integer25, float25.0 and signed zero-0.0, including nested int/float/boolean/null values, survive decoding and typed authoritative response, save/reload and fresh-store replay. Caller options remain unchanged. Metadata is retained without interpreting it as a new scientific definition.
- Malformed JSON, duplicate keys, NaN, overflow, underflow, array/boolean/number/string roots and mismatched typed structure_model reject. Strings are decoded once; a JSON string containing object text is not decoded again into an object.
- Literal `null` becomes actual null in stored source options, while the Evidence retains the existing explicit selected-model context. A direct awx record containing the transport string `"null"` rejects without writes. Canonical-format options do not receive the native-only decoding exception.
- A real authenticated loopback HTTP preview receives literal parameter text, returns the correct int/float/sign in serialized_bundle and performs no writes. Saving that exact authoritative bundle retains the same typed Evidence.

Command:

```powershell
& ./.venv/Scripts/python.exe -m pytest tests/test_predictions.py tests/test_predictions_independent.py tests/test_predictions_dto_independent.py -q --tb=short
```

Result: **82 passed in6.08s**: implementation51, prior independent17 and new DTO14. Log: `M5-predictions-domain-dto-independent-tests.log`; source identities and prior-hash comparisons: `M5-predictions-domain-dto-independent-source.json`. No product defect or scope escalation was found. The full original research action remains coherent: retain exact source and subject/model context for inspection and reproduction. The largest remaining gap is the complete independently replayed browser J08 workflow, followed by frozen-source regression and the separate scientific/user/release gates. This addendum does not advance the registered seven-flow/fourteen-negative baseline.
