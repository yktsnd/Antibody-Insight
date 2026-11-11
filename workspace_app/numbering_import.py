"""ANARCI text import with original file, explicit bindings, and attestation."""

import copy
import hashlib
import re
from functools import lru_cache

from .domain import AA, SCHEMA, fields, identifier, new_id, now, require, source, text, validate_extension, validate_transport_size

FORMAT = "anarci_text"
HIT_HEADER = "#|species|chain_type|e-value|score|seqstart_index|seqend_index|"
DOMAIN_HEADER = re.compile(r"# Domain ([1-9][0-9]*) of ([1-9][0-9]*)")
POSITION = re.compile(r"([HL])\s+([1-9][0-9]{0,2})\s+(?:([A-Z]{1,2})\s+)?([A-Z-])")
CHAIN_TYPES = {"H": "heavy", "K": "light", "L": "light"}
MAX_FILE_BYTES = 24 * 1024 * 1024
MAX_DOMAINS = 10000


def source_digest(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _coordinate(number, suffix):
    if not suffix:
        return ""
    require(number in (111, 112) and len(set(suffix)) == 1,
            "Unsupported ANARCI insertion outside the IMGT 111/112 extension convention")
    extension = ord(suffix[0]) - ord("A") + 1 + (len(suffix) - 1) * 26
    return f".{extension}"


def _domain(lines, ordinal):
    require(len(lines) >= 4 and lines[0] == "# Most significant HMM hit" and lines[1] == HIT_HEADER,
            "ANARCI domain is missing its HMM hit metadata")
    hit = lines[2].split("|")
    require(len(hit) == 8 and hit[0] == "#" and hit[-1] == "", "Malformed ANARCI HMM hit row")
    require(hit[2] in CHAIN_TYPES, "ANARCI domain is not an antibody H/K/L chain")
    require(all(re.fullmatch(r"[0-9]{1,6}", value) for value in hit[5:7]),
            "ANARCI requires original sequence start and end indexes")
    start, end = (int(value) + 1 for value in hit[5:7])
    require(1 <= start <= end <= 100000, "Invalid ANARCI inclusive sequence interval")
    schemes = [line for line in lines if line.startswith("# Scheme")]
    require(schemes == ["# Scheme = imgt"], "Each ANARCI domain must declare the IMGT scheme")
    scheme_index = lines.index(schemes[0])
    optional_metadata = lines[3:scheme_index]
    if optional_metadata:
        require(len(optional_metadata) == 3 and optional_metadata[0] == "# Most sequence-identical germlines" and
                optional_metadata[1] == "#|species|v_gene|v_identity|j_gene|j_identity|" and
                optional_metadata[2].startswith("#|"), "Malformed ANARCI germline metadata")
    coordinates = lines[scheme_index + 1:]
    chain_type = CHAIN_TYPES[hit[2]]
    entries = []
    for line in coordinates:
        if line.startswith("# Warning:") and len(coordinates) == 1:
            break
        match = POSITION.fullmatch(line)
        require(match is not None, "Malformed ANARCI residue coordinate")
        chain, number_text, insertion, aa = match.groups()
        require(chain == ("H" if chain_type == "heavy" else "L"), "ANARCI coordinate chain disagrees with HMM chain type")
        if aa == "-":
            continue
        require(aa in AA, "Invalid amino acid in ANARCI coordinate")
        number = int(number_text)
        entries.append({"sequence_index": start + len(entries), "aa": aa,
                        "number": number, "ins_code": _coordinate(number, insertion)})
    require(not entries or len(entries) == end - start + 1,
            "ANARCI residues do not span its declared inclusive source interval")
    return {"domain_index": ordinal, "chain_type": chain_type, "source_chain_type": hit[2],
            "sequence_start": start, "sequence_end": end, "entries": entries}


@lru_cache(maxsize=4)
def parse_anarci(content):
    require(isinstance(content, str) and 0 < len(content.encode("utf-8")) <= MAX_FILE_BYTES,
            "ANARCI text must contain 1–24 MiB of UTF-8")
    blocks, block = [], []
    for raw_line in content.removeprefix("\ufeff").splitlines():
        line = raw_line.strip()
        if line == "//":
            require(bool(block), "Empty ANARCI record")
            blocks.append(block)
            block = []
        elif line:
            block.append(line)
    require(not block and bool(blocks), "ANARCI records must end with //")
    require(len(blocks) <= MAX_DOMAINS, "Too many ANARCI records")
    domains = {}
    for record_index, lines in enumerate(blocks):
        require(lines[0].startswith("# ") and len(lines[0]) > 2, "ANARCI record identifier is missing")
        record_name = lines[0][2:]
        text(record_name, "ANARCI record identifier", 500)
        if len(lines) == 1:
            domains[(record_index, 0)] = {"record_index": record_index, "domain_index": 0,
                                          "record_name": record_name, "entries": []}
            continue
        require(lines[1] == "# ANARCI numbered", "ANARCI numbering marker is missing")
        headers = [(i, match) for i, line in enumerate(lines) if (match := DOMAIN_HEADER.fullmatch(line))]
        require(bool(headers) and headers[0][0] == 2, "ANARCI domain boundary is missing")
        for ordinal, (offset, match) in enumerate(headers, 1):
            require(match.groups() == (str(ordinal), str(len(headers))), "ANARCI domain sequence is incomplete or duplicated")
            end = headers[ordinal][0] if ordinal < len(headers) else len(lines)
            domain = _domain(lines[offset + 1:end], ordinal)
            domains[(record_index, ordinal)] = {**domain, "record_index": record_index, "record_name": record_name}
        require(len(domains) <= MAX_DOMAINS, "Too many ANARCI domains")
    return domains


def _binding(binding):
    fields(binding, {"record_index", "domain_index", "molecule_id", "chain_id", "verification"}, "numbering binding")
    require(type(binding["record_index"]) is int and 0 <= binding["record_index"] < MAX_DOMAINS,
            "Invalid numbering source record index")
    require(type(binding["domain_index"]) is int and 1 <= binding["domain_index"] <= MAX_DOMAINS,
            "Invalid numbering source domain index")
    identifier(binding["molecule_id"], "molecule")
    text(binding["chain_id"], "numbering target chain", 100)
    require(isinstance(binding["verification"], dict) and
            binding["verification"].get("status") in ("source_verified", "unverified"),
            "Use an actual source review record or keep imported numbering unverified")
    return binding["record_index"], binding["domain_index"]


def _map_payload(file_record, binding, domain):
    require(domain is not None and bool(domain["entries"]), "This ANARCI domain has no numbering to bind")
    return {
        "molecule_id": binding["molecule_id"], "chain_id": binding["chain_id"],
        "domain_id": f"ANARCI record {binding['record_index'] + 1} domain {binding['domain_index']}",
        "chain_type": domain["chain_type"], "scheme": "IMGT", "definition": "rearranged_v_domain",
        "status": "mapped", "reason": None,
        "sequence_start": domain["sequence_start"], "sequence_end": domain["sequence_end"],
        "source": file_record["source"], "verification": binding["verification"],
        "entries": domain["entries"],
        "numbering_origin": {"file_id": file_record["id"], "record_index": binding["record_index"],
                             "domain_index": binding["domain_index"]},
    }


def validate_numbering_file(record):
    text(record["name"], "numbering filename", 500)
    require(record["file_format"] == FORMAT, "Unsupported numbering file format")
    source(record["source"], "numbering source")
    require(record["source"]["name"] == "ANARCI", "Numbering source must identify ANARCI")
    require(isinstance(record["content"], str), "ANARCI file content must be text")
    parse_anarci(record["content"])
    require(record["sha256"] == source_digest(record["content"]), "Numbering source digest mismatch")
    allocations = record["allocations"]
    require(isinstance(allocations, list) and 0 < len(allocations) <= MAX_DOMAINS, "Numbering file requires domain allocations")
    for allocation in allocations:
        fields(allocation, {"map_id", "binding"}, "numbering allocation")
        identifier(allocation["map_id"], "residue_map")
        _binding(allocation["binding"])


def validate_numbering_origins(index):
    claimed = set()
    for file_record in index.values():
        if file_record["type"] != "numbering_file":
            continue
        domains = parse_anarci(file_record["content"])
        bound = set()
        for allocation in file_record["allocations"]:
            binding, map_id = allocation["binding"], allocation["map_id"]
            position = _binding(binding)
            require(position not in bound and map_id not in claimed, "Duplicate numbering source allocation")
            bound.add(position)
            claimed.add(map_id)
            record = index.get(map_id)
            require(record is not None and record["type"] == "residue_map", "Numbering source allocation lacks its residue map")
            expected = _map_payload(file_record, binding, domains.get(position))
            require(all(record.get(key) == value for key, value in expected.items()),
                    "Residue map differs from its retained ANARCI source or binding")
    require(all("numbering_origin" not in record or record["id"] in claimed for record in index.values()),
            "Numbering origin lacks its source allocation")


def anarci_preview(bundle, content, filename, version, bindings, bindings_text_sha256):
    text(filename, "numbering filename", 500)
    require(isinstance(content, str), "ANARCI file content must be text")
    domains = parse_anarci(content)
    digest = source_digest(content)
    tool = {"name": "ANARCI", "version": version}
    source(tool, "numbering source")
    require(isinstance(bindings, list) and len(bindings) <= MAX_DOMAINS, "Invalid numbering bindings")
    require(not bindings or bindings_text_sha256 == digest, "ANARCI text changed. Review and bind the current source.")
    project = bundle["project"]
    stamp = now()
    file_record = {"id": new_id("numbering_file"), "type": "numbering_file", "project_id": project["id"], "created_at": stamp,
                   "name": filename, "file_format": FORMAT, "content": content, "sha256": digest,
                   "source": tool, "allocations": []}
    records, bound = [], set()
    for binding in bindings:
        position = _binding(binding)
        require(position not in bound, "Bind each ANARCI domain once")
        bound.add(position)
        record = {**copy.deepcopy(_map_payload(file_record, binding, domains.get(position))),
                  "id": new_id("residue_map"), "type": "residue_map", "project_id": project["id"], "created_at": stamp}
        records.append(record)
        file_record["allocations"].append({"map_id": record["id"], "binding": binding})
    incoming = [file_record, *records] if records else []
    if incoming:
        validate_extension(project, bundle["entities"], incoming)
        validate_transport_size(project, [*bundle["entities"], *incoming])
    report = {"kind": FORMAT, "total_rows": len(domains), "valid_rows": len(records), "text_sha256": digest,
              "duplicates": [], "warnings": [], "excluded": [], "numbering_domains": []}
    for position, domain in domains.items():
        descriptor = {key: value for key, value in domain.items() if key != "entries"}
        descriptor["residue_count"] = len(domain["entries"])
        if not domain["entries"] or (records and position not in bound):
            report["excluded"].append({**descriptor, "reason": "No numbering returned" if not domain["entries"] else "No explicit target assigned"})
        elif not records:
            report["numbering_domains"].append(descriptor)
    return {"bundle": {"schema_version": SCHEMA, "project": project, "entities": incoming}, "report": report}
