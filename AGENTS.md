# AGENTS.md — Rules for Coding Agents

## Mission and hierarchy

Read in order: `PRODUCT_GOAL.md` → `DEVELOPMENT_PLAN.md` → active scenario (J01–J08) → acceptance criterion (AC) → `TRACEABILITY.csv` → latest ADR → open test failures. Never replace the mission with assumptions from prior implementations or chat history.

## Before starting any change

1. Write the affected `P-ID`, `J-ID`, and `AC-ID`. If any is missing, do not start a feature. Security/bug fixes may refer to an existing AC.
2. State the user action, visible result, input, output, affected data entities, and non-goals.
3. Define one happy-path test and at least two boundary/negative tests.
4. Check the mandatory gates: identity, provenance, security, regression. Any failure blocks the change.
5. Apply the 100-point priority rubric in `DEVELOPMENT_PLAN.md` for discretionary features; 80+ is first-tier, 60–79 is second-tier, <=59 backlog.

## Non-negotiable rules

- A protein sequence, molecular format, expression construct, and experiment material are not interchangeable identifiers.
- Measured, computed, literature-derived, annotations, hypotheses, and decisions must remain distinct.
- Never silently fill missing data with 0, fake a prediction, fabricate confidence, or copy parent measured data to a child as measured.
- Keep selection context across Explorer (E), Workspace (W), Design (D), and Decision (R).
- Do not alter the four-screen architecture, external-network default, data meaning, or scientific definitions without the specified approval.
- Keep existing tests. If any main flow regresses, do not merge.
- The default is no network transmission of proprietary sequences or experiments.

## Independent verification

A separate reviewer (agent with fresh context or human) must verify each milestone and substantial domain change. Reviewer independently replays the AC and proposes at least two new edge cases. Result must be `PASS`, `FAIL`, or `NEEDS-EVIDENCE`. Only `PASS` qualifies for integration. Where no independent reviewer is available, report `implemented / verification pending`, never `complete`.

## Stop-and-escalate conditions

Stop and request a decision if a change affects product mission, personas, primary journeys, molecular identity, provenance semantics, sharing of data, licensing, or scientific validity. On repeated same-cause test failure twice, pause changes and investigate. Limit unresolved architectural experiments to two engineer-days equivalent then report evidence and options; never invent scientific assumptions to force a conclusion.

## Done means

- P/J/AC traceability exists; tests and evidence are stored.
- The specified E2E path works with persisted real data (or clearly labeled fixtures).
- Its negative cases pass and existing flows still pass.
- No open P0/P1 bugs; independent reviewer returns PASS.
- Update TRACEABILITY, ADR (if applicable), known limitations, and release notes.

## Release 1.0 gates

Eight main flows pass (8/8). Sixteen listed negative flows pass (16/16). All evidence has type/source/timestamp/subject. Zero critical or high defects. Independent review complete. See plan for coverage, latency, storage, security, and human-user evaluation criteria.
