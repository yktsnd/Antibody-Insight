# Numeric transport correction: independent review

Verdict: **PASS for the bounded browser transport correction and tested guards.** Full M4, J06/J08 and integration on the eventual frozen source remain **NEEDS-EVIDENCE**.

Reviewer: `/root/observation_review`. Date: 2026-11-04, Asia/Tokyo. Scope: existing F05/F09 record/context fidelity and J06/J08 provenance/roundtrip requirements. Product-code edits were made only by the implementation agent; this reviewer added tests/evidence. Unrelated new experiment/measurement domain work is outside this transport verdict. No broad suite was rerun before the planned M4 freeze.

## Verified behavior

The earlier defect is preserved in `M4-numeric-transport-investigation.md` and `M4-numeric-transport-before-fix-browser-results.json`/`-run.log`. Actual raw JSON preview preserved integer1 versus float1.0 and nested signed zero; browser save/export collapsed them, causing two deliberately type-distinct server contexts to merge into one. This was a contract inconsistency, not proof of different physical quantities or changed experimental magnitudes.

I independently replayed `node tests/numeric-transport-browser.cjs` after the correction: **PASS, exit0**. Every Python-inspected typed canonical digest now matches its source through actual browser preview, save, native download and fresh-database file reimport. Dose types remain int/float, nested values retain int/float/negative-float-zero/float-zero, and both server cohorts and the actual imported UI context count remain2. A separately seeded typed store independently verifies export rather than merely re-exporting already-normalized data.

Evidence: `M4-numeric-transport-browser-results.json` and `M4-numeric-transport-independent-run.log`. Inspection uses raw response/file text parsed by Python, explicit type/sign checks and the actual observation-context function. JavaScript deep equality is not used to certify numeric type preservation.

## Guard review and independent edges

The implementation retains authoritative server JSON in a volatile WeakMap keyed by the actual root bundle or server-provided top-level nested bundle/serialized companion. Normal parsed objects remain available for UI display. Known snapshots require an unchanged client fingerprint; edited approved snapshots fail closed and require another preview. Export fetches a fresh approved raw bundle. Plain direct objects keep their existing explicit JSON/server-validation path. There is no custom numeric parser, library, server preview cache, entity-schema transport field, new persisted snapshot or localStorage payload.

`node tests/numeric-transport-guards-browser.cjs`: **four groups PASS, exit0** (`M4-numeric-transport-guards-results.json`, `-run.log`):

1. Editing either a known root bundle or nested approved bundle rejects before any import HTTP request. The original database and typed source remain unchanged; a stale raw body cannot ignore the edit.
2. An intentionally mismatched top-level nested raw companion rejects before use. User data is not recursively treated as a transport companion. The companion remains authoritative server-envelope metadata rather than a scientific entity field.
3. Unknown/direct objects still reach strict server validation: an extra root field rejects atomically; a valid explicit client body stores its current declared name/conditions, preserving the original project. This path does not promise to reconstruct numeric spelling already absent from a plain JavaScript object.
4. A valid nested preview containing Japanese text, distinct μ/µ characters, Å, nested numbers and signed zero saves with its exact Python typed digest. Native fresh export preserves that digest. Scientific note text, metric names and transport companions do not enter localStorage.

These guard probes call the actual application API helper to exercise its boundary; the main regression independently uses actual import/save/export controls. A first guard-harness run omitted the diagnostic fixture's required nested field in its deliberate plain-client body. Restoring that test input fixed the harness without a product change or weakened assertion; the initial diagnostic is labelled `M4-numeric-transport-before-guard-fixture-correction.json`.

## Scope and remaining gates

The matching raw/client fingerprint is a consistency guard within the trusted local server response path, not a new cryptographic authentication claim. The server still validates actual import content and session/Origin/CSRF. The same Python type-aware context policy is preserved; the correction does not redefine scientific comparability or assign biological meaning to integer/float spelling.

No unresolved transport defect was identified within these tested paths. This PASS neither upgrades existing synthetic tests to human scientific validation nor finishes a researcher journey. Preserve the pre-fix failure evidence, include both browser regressions in the eventual frozen-source checks, and freshly replay affected existing journeys before integration. M4's construct/material comparison, measurement provenance, finalized decisions and full J06–J08 acceptance remain separately tracked.
