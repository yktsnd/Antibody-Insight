"""Labelled engineering layouts for J02, not scientific humanization examples."""

from .fixtures import fixture_id, numbering_bundle


def design_bundle():
    bundle = numbering_bundle()
    remap = {bundle["project"]["id"]: fixture_id("project", "design-project")}
    remap.update({record["id"]: fixture_id(record["type"], "design/" + record["id"]) for record in bundle["entities"]})
    def remapped(value):
        if isinstance(value, str): return remap.get(value, value)
        if isinstance(value, list): return [remapped(item) for item in value]
        if isinstance(value, dict): return {key: remapped(item) for key, item in value.items()}
        return value
    bundle = remapped(bundle)
    bundle["project"]["title"] = "[SYNTHETIC FIXTURE] Numbered parent and reference design"
    molecules = [e for e in bundle["entities"] if e["type"] == "molecule"]
    for i, molecule in enumerate(molecules):
        molecule["external_id"] = f"DES-{i + 1:03}"
        molecule["name"] = f"Synthetic design candidate {i + 1:03}"
    molecules[1].update(external_id="REF-001", name="Synthetic human-reference layout (not a biological human sequence)")
    molecules[2].update(external_id="DES-UNAVAILABLE", name="Synthetic numbering unavailable candidate")
    for record in bundle["entities"]:
        if record["type"] == "residue_map" and record["molecule_id"] == molecules[1]["id"]:
            entry = next(e for e in record["entries"] if e["number"] == 10 and e["ins_code"] == "")
            entry["aa"] = "V"
            chain = next(c for c in molecules[1]["chains"] if c["id"] == record["chain_id"])
            chain["sequence"] = chain["sequence"][:entry["sequence_index"] - 1] + "V" + chain["sequence"][entry["sequence_index"]:]
        if record["type"] == "residue_map" and record["molecule_id"] == molecules[2]["id"]:
            record.update(status="unavailable", reason="Synthetic source numbering failure", entries=[], sequence_start=None, sequence_end=None)
    return bundle
