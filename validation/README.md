# Human scientific and researcher validation

[日本語](README.ja.md) · [Original acceptance specification](../DEVELOPMENT_PLAN.md)

Engineering tests reconstruct records and exercise interface behavior. They do not establish scientifically correct annotations or usefulness in real research. Release1.0 remains unaccepted until the separate requirements below are met. No human reviewer or validation result has been invented.

Use the development app locally at http://127.0.0.1:8765 (or run start.ps1). Record the actual application commit/version and the submitted-source hashes in each review. Do not send proprietary sequences or experiments to external tools; the default remains local. Existing research records must not be overwritten for evaluation. Use an explicitly separate evaluation database and import local copies of suitable review inputs.

From a PowerShell window in the project folder, choose a new unused evaluation database filename and run:

```powershell
.\start.ps1 -Database "$env:LOCALAPPDATA\AntibodyInsight\human-evaluation.sqlite3" -Port 8766
```

Open http://127.0.0.1:8766 for that separate evaluation session. An existing database filename opens its existing records; use a distinct filename for a new evaluation.

## Eighteen human-verified fixed examples

SCIENTIFIC_GOLDENS.csv preserves the eighteen categories required by plan§10.1. All initially require an actual input, independently checked expected values, primary source/method and version, named human reviewer and date. A category label or synthetic engineering test is not a scientific golden. Unknown fields stay empty, never zero or an invented validation date.

For each supplied fixed example, review the exact molecule/construct/material identities, chain declarations, numbering scheme/domain/CDR definition if applicable, source-model/residue/insertion/alternate identities, evidence kind/unit/conditions/version/time and expected rejection/missingness behavior. Check the source directly. Record input hash, expected-result file, reviewer, review date and PASS/FAIL/NEEDS-EVIDENCE; retain the reviewed input and expectations locally. Import only annotations the reviewer has actually attested. Existing synthetic engineering fixtures must remain labelled synthetic and must not be relabelled human-validated.

The public experimental1MLC source is already pinned for offline parser/rendering scale checks. That automated check does not supply the eighteen reviewed goldens or validate a prediction. There is no claim of a humanness score, model accuracy, physical assembly, causal expression effect or coordinate-to-sequence inference.

## Eight-role researcher evaluation

RESEARCHER_EVALUATION.csv contains one task for each original persona and journey. A person may review several roles, but must perform each task separately and be identified for that task. Start from the stated research question, use actual local inputs, observe/compare/interpret and retain the next research action. Note completion, mistakes, points of hesitation, unresolved decisions and whether the result is scientifically useful. Test counts do not replace this evaluation; eight role reviews are an initial usability sample and do not establish statistical effectiveness.

Use the language switch in the researcher guide to review English/Japanese explanations. Preserve original scientific values, source text, metric names and identifiers. Humanization is ヒト化; humanness is ヒト抗体らしさ with its actual method-specific definition, if a future method exists.

Return the completed local review records and referenced input/expected-result paths for engineering follow-up. Missing reviewers or unsuitable inputs remain NEEDS-EVIDENCE. New product-purpose, identity, scientific-definition or sharing-policy choices require the requester decision specified in AGENTS.md; these worksheets do not authorize such changes.
