"""Independent ANARCI multi-domain and exact-byte probes in temporary stores."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from public_structure_fixture import public_structure_bundle
from workspace_app.domain import ValidationError
from workspace_app.numbering_import import anarci_preview
from workspace_app.storage import Store


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sequence(lines):
    return "".join(line.split()[-1] for line in lines if re.match(r"^[HL] ", line) and not line.endswith("-"))


def require_error(action, message):
    try:
        action()
    except ValidationError as exc:
        assert message in str(exc), str(exc)
    else:
        raise AssertionError("Expected rejection: " + message)


def main(output):
    project_bundle = public_structure_bundle()
    project = project_bundle["project"]
    project.update(data_class="synthetic_fixture", title="SYNTHETIC mixed-domain transport test")
    molecule = project_bundle["entities"][0]
    molecule.update(name="Synthetic light / heavy tandem", external_id="M7-SYNTHETIC-TANDEM")
    source = (ROOT / "fixtures/public/1MLC-AB.anarci.txt").read_bytes()
    assert digest(source) == "26c2c44b388d7f62dd9efdf992a1c69f366f07cc0db1b43001e32c175c3e0747"
    light_lines, heavy_lines = [block.strip().splitlines() for block in source.decode().split("//") if block.strip()]
    light = sequence(light_lines)
    heavy = sequence(heavy_lines)
    linker = "GGGGS"
    offset = len(light) + len(linker)
    molecule["chains"] = [{"id": "fusion", "role": "mixed domain", "sequence": light + linker + heavy}]
    molecule["source"] = {"name": "Synthetic assembly from real public variable segments", "version": None}
    baseline = {**project_bundle, "entities": [molecule]}
    first = light_lines[2:]
    first[0] = "# Domain 1 of 2"
    second = heavy_lines[2:]
    second[0] = "# Domain 2 of 2"
    hit = second[3].split("|")
    assert hit[2] == "H" and hit[5:7] == ["0", "115"]
    hit[5:7] = [str(offset), str(offset + len(heavy) - 1)]
    second[3] = "|".join(hit)
    content = "\ufeff" + "\r\n".join(
        ["# SYNTHETIC adapted native output", "# ANARCI numbered", *first, *second, "//", ""]
    )
    verification = {"status": "unverified", "reference": None, "reviewer": None, "reviewed_at": None}
    bindings = [{"record_index": 0, "domain_index": i, "molecule_id": molecule["id"],
                 "chain_id": "fusion", "verification": verification} for i in (1, 2)]
    results = []
    with tempfile.TemporaryDirectory(prefix="awx-ANARCI-independent-") as temp:
        store = Store(Path(temp) / "before.sqlite3")
        store.import_bundle(baseline)
        before = store.bundle(project["id"])
        assert before == baseline
        sha = digest(content.encode())
        preview = anarci_preview(before, content, "synthetic.adapted.anarci.txt", None, bindings, sha)
        native, light_map, heavy_map = preview["bundle"]["entities"]
        assert native["content"].encode() == content.encode()
        assert native["sha256"] == sha
        assert light_map["chain_type"] == "light" and heavy_map["chain_type"] == "heavy"
        assert (light_map["sequence_start"], light_map["sequence_end"]) == (1, len(light))
        assert (heavy_map["sequence_start"], heavy_map["sequence_end"]) == (offset + 1, offset + len(heavy))
        assert [entry["sequence_index"] for entry in heavy_map["entries"]] == list(range(offset + 1, offset + len(heavy) + 1))
        assert "".join(entry["aa"] for entry in heavy_map["entries"]) == heavy
        assert light_map["numbering_origin"]["domain_index"] == 1
        assert heavy_map["numbering_origin"]["domain_index"] == 2
        results.append("Same chain retains distinct light and heavy domains and an exact raw offset after a linker")

        invalid = content.replace("# Domain 2 of 2", "# Domain 1 of 2")
        require_error(lambda: anarci_preview(before, invalid, "duplicate.txt", None, [], None),
                      "domain sequence is incomplete or duplicated")
        stale = content.replace("\r\n", "\n")
        require_error(lambda: anarci_preview(before, stale, "changed.txt", None, bindings, sha), "text changed")
        assert store.bundle(project["id"]) == before
        results.append("Duplicate domain ordinals and changed line endings cannot reuse a binding")

        store.import_bundle(preview["bundle"])
        after = store.bundle(project["id"])
        fresh = Store(Path(temp) / "fresh.sqlite3")
        fresh.import_bundle(after)
        recovered = fresh.bundle(project["id"])
        assert recovered == after
        assert next(e for e in recovered["entities"] if e["type"] == "numbering_file")["content"].encode() == content.encode()
        results.append("UTF-8 BOM and CRLF remain byte-identical after persistence and fresh transfer")

    names = ["workspace_app/domain.py", "workspace_app/numbering.py", "workspace_app/numbering_import.py"]
    artifact = {
        "status": "PASS", "reviewer": "/root/deposited_mapping_review",
        "timestamp": datetime.now(timezone.utc).isoformat(), "results": results,
        "scope": "Synthetic mixed-domain input adapted from real source text and labelled as an engineering probe",
        "sha256": {name: digest((ROOT / name).read_bytes()) for name in names},
    }
    with output.open("x", encoding="utf-8", newline="") as file:
        file.write(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps(artifact, ensure_ascii=False))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
