"""Imported IMGT rearranged V-domain annotations. No numbering inference.

P01/P02/P08, J01/J02/J08, AC-J01/AC-J02/AC-J08, F07.
Regions: IMGT FR/CDR nomenclature source in docs/NUMBERING_CONTRACT.md.
"""

import re

from .domain import fields, identifier, nullable_text, require, source, text, timestamp

REGION_SOURCE = "https://www.imgt.org/IMGTScientificChart/Nomenclature/IMGT-FRCDRdefinition.html"
REGIONS = ((1, 26, "FR1"), (27, 38, "CDR1"), (39, 55, "FR2"), (56, 65, "CDR2"),
           (66, 104, "FR3"), (105, 117, "CDR3"), (118, 129, "FR4"))
DEFAULT_CHOICES = object()


def region_for(number):
    return next(label for low, high, label in REGIONS if low <= number <= high)


def coordinate_key(number, ins_code):
    if not ins_code:
        return number, 0, 0
    extension = int(ins_code[1:])
    return (111, 1, extension) if number == 111 else (111, 2, -extension)


def validate_numbering_shape(record):
    identifier(record["molecule_id"], "molecule")
    text(record["chain_id"], "residue_map.chain_id", 100)
    text(record["domain_id"], "residue_map.domain_id", 100)
    require(record["chain_type"] in ("heavy", "light", "unknown"), "Explicit chain type required")
    require(record["scheme"] == "IMGT" and record["definition"] == "rearranged_v_domain",
            "Unsupported numbering scheme/domain definition")
    require(record["status"] in ("mapped", "unavailable", "failed"), "Unsupported numbering status")
    nullable_text(record["reason"], "residue_map.reason")
    source(record["source"], "residue_map.source")
    verification = record["verification"]
    fields(verification, {"status", "reference", "reviewer", "reviewed_at"}, "verification")
    require(verification["status"] in ("source_verified", "unverified", "engineering_fixture"), "Unsupported map verification status")
    nullable_text(verification["reference"], "verification.reference")
    if verification["status"] == "source_verified":
        text(verification["reference"], "verification.reference")
        text(verification["reviewer"], "verification.reviewer", 500)
        timestamp(verification["reviewed_at"], "verification.reviewed_at")
    else:
        require(verification["reviewer"] is None and verification["reviewed_at"] is None,
                "Unverified/fixture maps must not carry a source-verified attestation")
    entries = record["entries"]
    require(isinstance(entries, list), "Numbering entries must be a list")
    if record["status"] != "mapped":
        require(entries == [] and record["sequence_start"] is None and record["sequence_end"] is None,
                "Unavailable/failed numbering cannot contain successful positions")
        text(record["reason"], "Numbering unavailable/failed reason")
        return
    start, end = record["sequence_start"], record["sequence_end"]
    require(type(start) is int and type(end) is int and 1 <= start <= end <= 100000,
            "Mapped domain requires an inclusive 1-based sequence interval")
    require(len(entries) == end - start + 1, "Mapped domain must cover every observed sequence residue")
    seen, previous = set(), None
    for expected_index, entry in enumerate(entries, start):
        fields(entry, {"sequence_index", "aa", "number", "ins_code"}, "residue_map.entry")
        require(type(entry["sequence_index"]) is int and entry["sequence_index"] == expected_index,
                "Numbering entries must follow contiguous raw sequence order")
        require(isinstance(entry["aa"], str) and len(entry["aa"]) == 1, "Mapped amino acid must be a single symbol")
        number, ins = entry["number"], entry["ins_code"]
        require(type(number) is int and 1 <= number <= 129, "IMGT V-domain position must be an integer from 1 to 129")
        require(isinstance(ins, str), "Insertion code must be preserved as text")
        require(not ins or (number in (111, 112) and re.fullmatch(r"\.[1-9][0-9]{0,2}", ins) is not None),
                "Unsupported IMGT insertion coordinate; only 111/112 decimal extensions are supported")
        coordinate = (number, ins)
        require(coordinate not in seen, "Duplicate IMGT coordinate in one domain")
        seen.add(coordinate)
        key = coordinate_key(number, ins)
        require(previous is None or previous < key, "IMGT coordinate order conflicts with observed sequence order")
        previous = key


def validate_numbering_references(project, index):
    for record in index.values():
        if record["type"] != "residue_map":
            continue
        molecule = index.get(record["molecule_id"])
        require(molecule is not None and molecule["type"] == "molecule", "Unknown or wrong-type numbered molecule")
        chain = next((c for c in molecule["chains"] if c["id"] == record["chain_id"]), None)
        require(chain is not None, "Numbered chain is not defined in the named molecule")
        if record["verification"]["status"] == "engineering_fixture":
            require(project.get("data_class", "research") == "synthetic_fixture",
                    "Engineering numbering fixture requires explicit synthetic_fixture project metadata")
        if record["status"] == "mapped":
            require(record["sequence_end"] <= len(chain["sequence"]), "Numbering interval exceeds the source chain")
            for entry in record["entries"]:
                require(chain["sequence"][entry["sequence_index"] - 1] == entry["aa"],
                        "Numbered amino acid differs from the named molecule/chain/raw index")


def observe_map(record, project):
    """Return transparent views of a validated imported map, retaining its identity."""
    entries = [{**entry, "coordinate": str(entry["number"]) + entry["ins_code"], "region": region_for(entry["number"])}
               for entry in record["entries"]]
    anchors = {entry["number"] for entry in record["entries"] if entry["ins_code"] == ""}
    complete = (record["status"] == "mapped" and {104, 118} <= anchors and
                any(entry["region"] == "CDR3" for entry in entries))
    verified = record["verification"]["status"] == "source_verified"
    fixture = record["verification"]["status"] == "engineering_fixture" and project.get("data_class") == "synthetic_fixture"
    eligible = record["status"] == "mapped" and (verified or fixture)
    cdr3 = "".join(entry["aa"] for entry in entries if entry["region"] == "CDR3") if complete else None
    return {"id": record["id"], "molecule_id": record["molecule_id"], "chain_id": record["chain_id"],
            "domain_id": record["domain_id"], "chain_type": record["chain_type"], "scheme": record["scheme"],
            "definition": record["definition"], "status": record["status"], "reason": record["reason"],
            "verification": record["verification"], "source": record["source"], "entries": entries,
            "eligible": eligible, "cdr3_complete": complete, "cdr3_sequence": cdr3,
            "region_source": REGION_SOURCE}


def observations(bundle):
    return {"maps": [observe_map(record, bundle["project"]) for record in bundle["entities"] if record["type"] == "residue_map"]}


def cdr3_groups(bundle, choices=DEFAULT_CHOICES):
    """No first-map fallback when several heavy domains or map versions exist."""
    if choices is DEFAULT_CHOICES:
        choices = {}
    require(isinstance(choices, dict), "Map choices must be an object keyed by molecule ID")
    molecule_ids = {e["id"] for e in bundle["entities"] if e["type"] == "molecule"}
    require(all(isinstance(key, str) and key in molecule_ids for key in choices), "Map choices contain an unknown molecule ID")
    require(all(isinstance(value, str) and bool(value.strip()) for value in choices.values()), "Map choices must contain non-empty map IDs")
    observed = observations(bundle)["maps"]
    result, groups, group_ids = [], {}, {}
    for molecule in (e for e in bundle["entities"] if e["type"] == "molecule"):
        maps = [m for m in observed if m["molecule_id"] == molecule["id"] and m["chain_type"] == "heavy" and m["eligible"]]
        chosen_id = choices.get(molecule["id"])
        if chosen_id is not None:
            match = next((m for m in maps if m["id"] == chosen_id), None)
            require(match is not None, "Selected CDR-H3 map is unavailable, unverified, or not a heavy-chain domain")
        elif len(maps) == 1:
            match = maps[0]
        else:
            match = None
        status = "mapping unavailable" if not maps else "choose map/domain" if match is None else "partial CDR3"
        group = None
        if match is not None and match["cdr3_complete"]:
            group, status = match["cdr3_sequence"], "mapped"
            groups.setdefault(group, []).append(molecule["id"])
            group_ids.setdefault(group, match["id"])
        result.append({"molecule_id": molecule["id"], "status": status, "map_id": match["id"] if match else None,
                       "cdr3_sequence": group, "options": [{"id": m["id"], "chain_id": m["chain_id"], "domain_id": m["domain_id"],
                                                              "verification": m["verification"]["status"]} for m in maps]})
    return {"candidates": result, "groups": [{"group_id": group_ids[sequence], "cdr3_sequence": sequence, "candidate_ids": ids}
                                             for sequence, ids in sorted(groups.items())]}
