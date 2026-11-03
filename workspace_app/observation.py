"""Read-only ordering of explicit observations; no aggregation or conversion."""

from __future__ import annotations

import json

from .domain import molecule_id_for, require

DEFAULT_CHOICES = object()


def context_issue(record):
    if record["kind"] not in ("measured", "computed"):
        return "not a measured or computed observation"
    if not record["unit"] or not record["unit"].strip():
        return "unit unknown"
    if record["source"]["version"] is None:
        return "source version unknown"
    conditions = record["conditions"]
    if not isinstance(conditions, dict) or not isinstance(conditions.get("assay"), str) or not conditions["assay"].strip():
        return "assay / conditions unknown"
    return None


def context_key(record):
    # JSON retains bool versus number and int versus float; dict order is immaterial.
    return json.dumps([record["kind"], record["metric"], record["unit"], record["conditions"], record["source"]],
                      sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def observation_order(bundle, cohort_id=None, choices=DEFAULT_CHOICES, direction="ascending"):
    """Return original scalar values and IDs only when one observation is explicit.

    Exact metadata equality is an ordering policy, not scientific validation of an
    assay or a claim that the samples are interchangeable.
    """
    if choices is DEFAULT_CHOICES:
        choices = {}
    require(cohort_id is None or (isinstance(cohort_id, str) and bool(cohort_id.strip())), "Cohort ID must be null or a non-empty Evidence ID")
    require(direction in ("ascending", "descending"), "Direction must be ascending or descending")
    require(isinstance(choices, dict), "Observation choices must be an object keyed by molecule ID")
    index = {record["id"]: record for record in bundle["entities"]}
    molecules = [record for record in index.values() if record["type"] == "molecule"]
    molecule_ids = {record["id"] for record in molecules}
    require(all(isinstance(key, str) and key in molecule_ids for key in choices), "Observation choices contain an unknown molecule ID")
    require(all(isinstance(value, str) and bool(value.strip()) for value in choices.values()), "Observation choices require non-empty Evidence IDs")
    require(cohort_id is not None or not choices, "Choose a context before an observation")
    evidence = [record for record in index.values() if record["type"] == "evidence"]
    eligible, cohorts, by_molecule, issues = {}, {}, {}, []
    for record in sorted(evidence, key=lambda item: item["id"]):
        molecule_id = molecule_id_for(index[record["subject_id"]], index)
        if molecule_id is None:
            continue
        by_molecule.setdefault(molecule_id, []).append(record)
        issue = context_issue(record)
        if issue:
            issues.append({"evidence_id": record["id"], "molecule_id": molecule_id, "reason": issue})
            continue
        key = context_key(record)
        eligible[record["id"]] = key
        if key not in cohorts:
            cohorts[key] = {"id": record["id"], "kind": record["kind"], "metric": record["metric"],
                            "unit": record["unit"], "conditions": record["conditions"], "source": record["source"], "evidence_ids": []}
        cohorts[key]["evidence_ids"].append(record["id"])
    require(cohort_id is None or cohort_id in eligible, "Selected context is unavailable or incomplete; choose a context explicitly")
    selected_key = eligible.get(cohort_id)
    rows = []
    for molecule in molecules:
        records = by_molecule.get(molecule["id"], [])
        options = [record for record in records if selected_key is not None and eligible.get(record["id"]) == selected_key]
        chosen_id = choices.get(molecule["id"])
        chosen = None
        if chosen_id is not None:
            chosen = next((record for record in options if record["id"] == chosen_id), None)
            require(chosen is not None, "Selected observation is stale, belongs to another candidate, or is outside the chosen context")
        elif len(options) == 1:
            chosen = options[0]
        status = ("not measured / not predicted" if not records else "choose context" if selected_key is None else
                  "choose observation" if len(options) > 1 and chosen is None else
                  "value missing" if chosen is not None and chosen["value"] is None else
                  "observed" if chosen is not None else
                  "different context" if any(record["id"] in eligible for record in records) else "context incomplete")
        rows.append({"molecule_id": molecule["id"], "status": status, "evidence_id": chosen["id"] if chosen else None,
                     "value": chosen["value"] if chosen else None, "unit": chosen["unit"] if chosen else None,
                     "options": [{"id": record["id"], "subject_id": record["subject_id"], "value": record["value"],
                                  "unit": record["unit"], "timestamp": record["timestamp"]} for record in options]})
    labels = {record["id"]: (record["external_id"], record["id"]) for record in molecules}
    sign = -1 if direction == "descending" else 1
    rows.sort(key=lambda row: (row["value"] is None, sign * row["value"] if row["value"] is not None else 0, labels[row["molecule_id"]]))
    return {"cohort_id": cohort_id, "cohorts": list(cohorts.values()), "candidates": rows, "ineligible": issues, "direction": direction}
