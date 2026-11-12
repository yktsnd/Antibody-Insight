"""Replay the declared composition contract against a public GSRS record."""

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from workspace_app.adapters import grouped_fasta_preview, new_project
from workspace_app.assembly import composition_context, composition_preview
from workspace_app.domain import SCHEMA, ValidationError, new_id, now
from workspace_app.storage import Store


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "validation" / "public"
REGISTRY = "https://gsrs.ncats.nih.gov/api/v1/substances(7NL2E3F6K3)"
SOURCE_SHA256 = "696d14a3c129ea3924ff675378c91eb7428dd42e8ff8592affed8af453149322"


def source_units(molecule):
    chains = {chain["id"]: chain for chain in molecule["chains"]}
    for heavy, light in (("Q", "L1"), ("J", "L2")):
        components = []
        for name in (heavy, light):
            chain = chains[name]
            components.append({
                "id": name,
                "role": chain["role"],
                "sequence": chain["sequence"],
                "origin": {
                    "molecule_id": molecule["id"],
                    "chain_id": name,
                    "start": 1,
                    "end": len(chain["sequence"]),
                },
            })
        yield {
            "id": new_id("binding_unit"),
            "type": "binding_unit",
            "project_id": molecule["project_id"],
            "created_at": now(),
            "name": f"Source chain pair {heavy} / {light}",
            "topology": "paired",
            "source": {"name": REGISTRY, "version": f"GSRS 37 sha256:{SOURCE_SHA256}"},
            "chains": components,
        }


def declared_composition(units):
    chains = []
    for unit in units:
        for chain in unit["chains"]:
            chains.append({
                "id": chain["id"],
                "role": chain["role"],
                "copies": 1,
                "components": [{
                    "id": f"source-{chain['id']}",
                    "role": "complete mature chain",
                    "source": {
                        "kind": "binding_unit",
                        "binding_unit_id": unit["id"],
                        "chain_id": chain["id"],
                        "start": 1,
                        "end": len(chain["sequence"]),
                    },
                }],
            })
    connections = [
        {
            "left": {"chain_id": left, "component_id": f"source-{left}"},
            "right": {"chain_id": right, "component_id": f"source-{right}"},
            "kind": "disulfide",
        }
        for left, right in (("Q", "L1"), ("J", "L2"), ("Q", "J"))
    ]
    return {
        "name": "Emicizumab registry composition",
        "external_id": "EMI-DECLARED",
        "format": "Asymmetric bispecific IgG4",
        "chains": chains,
        "connections": connections,
        "parent_id": None,
        "reason": None,
        "note": "Registry-derived chain and component declaration. The original registry contains residue-level disulfides.",
    }


def run(directory):
    raw = (SOURCE_DIR / "emicizumab-gsrs.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA256
    protein = json.loads(raw)["protein"]
    names = ("Q", "J", "L1", "L2")
    subunits = {index: item["sequence"] for index, item in enumerate(protein["subunits"], 1)}
    assert [len(value) for value in subunits.values()] == [448, 444, 214, 214]
    assert subunits[3] == subunits[4] and subunits[1] != subunits[2]

    project = new_project("Public bispecific reference", "Inspect composition against the NIH GSRS record")
    assignments = [
        {"record_index": index, "external_id": "EMI-GSRS", "chain_id": name,
         "role": "heavy" if index < 2 else "light"}
        for index, name in enumerate(names)
    ]
    fasta = (SOURCE_DIR / "emicizumab.fasta").read_bytes()
    source = grouped_fasta_preview(
        fasta.decode("ascii"), "emicizumab.fasta", project,
        {"molecular_format": "Asymmetric bispecific IgG4", "assignments": assignments,
         "text_sha256": hashlib.sha256(fasta).hexdigest()},
    )["bundle"]
    molecule, = source["entities"]
    assert {chain["id"]: chain["sequence"] for chain in molecule["chains"]} == dict(zip(names, subunits.values()))
    units = list(source_units(molecule))

    db = directory / "original.sqlite3"
    store = Store(db)
    store.import_bundle(source)
    store.import_bundle({"schema_version": SCHEMA, "project": project, "entities": units})
    base = store.bundle(project["id"])
    definition = declared_composition(units)
    preview = composition_preview(base, definition)
    assert store.bundle(project["id"]) == base
    store.import_bundle(preview)
    saved = Store(db).bundle(project["id"])
    fresh = Store(directory / "restored.sqlite3")
    fresh.import_bundle(saved)
    assert fresh.bundle(project["id"]) == saved

    designed = preview["entities"][0]
    graph = designed["component_graph"]
    context = composition_context(saved, designed["id"])
    assert context["status"] == "declared"
    assert {unit["unit"]["id"] for unit in context["source_units"]} == {unit["id"] for unit in units}
    assert all(chain["copies"] == 1 for chain in graph["chains"])
    assert {chain["id"]: chain["sequence"] for chain in designed["chains"]} == dict(zip(names, subunits.values()))
    assert all(record["kind"] == "annotation" for record in saved["entities"] if record["type"] == "evidence")

    declared_pairs = {tuple(sorted((connection["left"]["chain_id"], connection["right"]["chain_id"])))
                      for connection in graph["connections"]}
    original_pairs = set()
    interchain_bonds = 0
    for link in protein["_disulfideLinks"]["shorthand"].split(";"):
        first, second = [tuple(map(int, site.split("_"))) for site in link.split("->")]
        assert all(subunits[chain][index - 1] == "C" for chain, index in (first, second))
        if first[0] != second[0]:
            interchain_bonds += 1
            original_pairs.add(tuple(sorted((names[first[0] - 1], names[second[0] - 1]))))
    assert declared_pairs == original_pairs
    assert interchain_bonds == 4 and len(declared_pairs) == 3

    missing_light = {**definition, "chains": [chain for chain in definition["chains"] if chain["id"] != "L2"]}
    try:
        composition_preview(saved, missing_light)
    except ValidationError as error:
        assert "Connection endpoint is not defined" in str(error)
    else:
        raise AssertionError("An absent light-chain endpoint was accepted")
    assert store.bundle(project["id"]) == saved

    return {
        "status": "PASS",
        "scope": "Developer preflight of declared composition using public source data",
        "source_sha256": SOURCE_SHA256,
        "chain_lengths": dict(zip(names, map(len, subunits.values()))),
        "original_interchain_disulfides": interchain_bonds,
        "retained_component_pairs": sorted(declared_pairs),
        "separate_equal_sequence_light_chains": True,
        "read_only_preview": True,
        "missing_endpoint_rejected": True,
        "restart_and_fresh_store_equal": True,
        "human_validation": "pending",
        "residue_level_bond_identity": "requires original registry",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="awx-emicizumab-") as directory:
        result = json.dumps(run(Path(directory)), indent=2) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8", newline="\n")
    print(result, end="")
