"""Explicit source-reported evidence positions. No sequence/structure inference."""

from .domain import fields, require, text


def validate_evidence_position_shape(positions):
    require(isinstance(positions, list) and len(positions) <= 1000, "Evidence residue_refs must contain up to 1000 explicit positions")
    seen = set()
    for position in positions:
        fields(position, {"chain_id", "sequence_index"}, "Evidence residue reference")
        text(position["chain_id"], "Evidence residue chain", 100)
        require(type(position["sequence_index"]) is int and 1 <= position["sequence_index"] <= 100000,
                "Evidence residue index must be a 1-based integer")
        key = position["chain_id"], position["sequence_index"]
        require(key not in seen, "Duplicate Evidence residue reference")
        seen.add(key)


def validate_evidence_position_references(evidence, molecule):
    for position in evidence.get("residue_refs", []):
        chain = next((c for c in molecule["chains"] if c["id"] == position["chain_id"]), None)
        require(chain is not None and position["sequence_index"] <= len(chain["sequence"]),
                "Reported residue is unavailable on the Evidence's own molecule/chain")
