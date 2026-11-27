"""Read local sequence records without inferring molecular identity or pairing."""
import csv
import hashlib
import io
import math
import warnings
import zipfile

from Bio import SeqIO
from Bio.Data.CodonTable import TranslationError
from Bio.Seq import complement
from Bio.SeqFeature import AfterPosition, BeforePosition, ExactPosition
from Bio.SeqIO import SnapGeneIO
from Bio.SeqRecord import SeqRecord
from defusedxml.minidom import parseString
from openpyxl import load_workbook

LIMIT = 24 * 1024 * 1024
ALPHABETS = {"DNA": set("ACGTRYSWKMBDHVN"), "AA": set("ACDEFGHIKLMNPQRSTVWYBXZJUO*")}
SEQ_COLUMNS = ("candidate", "component", "kind", "sequence")
OBS_COLUMNS = ("candidate", "metric", "value", "unit", "kind", "sample", "conditions", "source", "event_time")
MEASUREMENT_COLUMNS = OBS_COLUMNS + ("replicate_set", "statistic", "error_type", "error", "n")
STRUCTURE_COLUMNS = ("metric","value","unit","region","conditions","source")


def sequence(value, kind):
    seq = "".join(value.split()).upper()
    if kind not in ALPHABETS or not seq or set(seq) - ALPHABETS[kind]:
        raise ValueError(f"Invalid {kind} sequence.")
    return seq


def record(candidate, component, kind, seq, features=None, topology=None):
    if not candidate.strip() or not component.strip():
        raise ValueError("Candidate key and component label are required.")
    return dict(candidate=candidate.strip(), component=component.strip(), kind=kind,
                sequence=sequence(seq, kind), features=features or [], topology=topology)


def rows(data, extension):
    if extension == ".xlsx":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if sum(info.file_size for info in archive.infolist()) > LIMIT:
                raise ValueError("Workbook exceeds the expanded size limit.")
            if len(archive.infolist()) > 1000:
                raise ValueError("Too many workbook parts.")
        workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=False, keep_links=False)
        try:
            if len(workbook.worksheets) != 1:
                raise ValueError("Use a single worksheet matching the template.")
            sheet = workbook.worksheets[0]
            sheet.reset_dimensions()
            for row in sheet.rows:
                if any(cell.data_type in {"f", "e"} for cell in row):
                    raise ValueError("Replace formulas and spreadsheet errors with explicit values.")
                yield ["" if cell.value is None else str(cell.value).strip() for cell in row]
        finally:
            workbook.close()
    else:
        yield from csv.reader(io.StringIO(data.decode("utf-8-sig")), delimiter="\t" if extension == ".tsv" else ",")


def observation(row):
    from datetime import datetime
    value = float(row["value"]) if row["value"] else None
    if value is not None and not math.isfinite(value):
        raise ValueError("Observation values must be finite or blank.")
    kind = row["kind"]
    if kind not in {"Measured", "Computed", "Reference measured", "Reference computed"}:
        raise ValueError("Specify the observation kind from the template.")
    if not all(row[k] for k in ("candidate", "metric", "unit", "source")):
        raise ValueError("Candidate, metric, unit and source are required.")
    statistic = row.get("statistic","Individual")
    if statistic == "Individual" and kind in {"Measured", "Reference measured"} and not row["sample"]:
        raise ValueError("A measured record requires its original sample.")
    if row["event_time"] and datetime.fromisoformat(row["event_time"]).utcoffset() is None:
        raise ValueError("Include a time zone or leave the event time blank.")
    if "statistic" not in row:
        return dict(row, value=value)
    if statistic not in {"Individual", "Mean"} or kind not in {"Measured","Reference measured"}:
        raise ValueError("Use Individual or Mean for measured results.")
    if statistic == "Individual" and any(row[k] for k in ("error_type","error","n")):
        raise ValueError("An individual reading cannot carry summary statistics.")
    if statistic == "Mean" and value is None:
        raise ValueError("A reported mean needs a numeric value.")
    error_type = row["error_type"]
    error = float(row["error"]) if row["error"] else None
    if error_type not in {"","SD","SEM"} or bool(error_type) != (error is not None):
        raise ValueError("Supply an error together with its SD or SEM definition.")
    if error is not None and (not math.isfinite(error) or error < 0):
        raise ValueError("Error must be finite and nonnegative.")
    n = row["n"]
    if n and (not n.isascii() or not n.isdecimal() or not 1 <= int(n) <= 2**53-1):
        raise ValueError("Measurement count must be a positive whole number.")
    return dict(row,value=value,error=error,n=int(n) if n else None)


def structural_value(row):
    if not all(row[k] for k in STRUCTURE_COLUMNS):
        raise ValueError("Every structure metric field is required.")
    value=float(row["value"])
    if not math.isfinite(value):
        raise ValueError("Structure metrics must be finite.")
    return dict(row,value=value)


def structured(data, ext):
    iterator = rows(data, ext)
    try:
        header = tuple(next(iterator, []))
        if header not in (SEQ_COLUMNS, OBS_COLUMNS, MEASUREMENT_COLUMNS, STRUCTURE_COLUMNS):
            raise ValueError("Column headings must match a supported template.")
        mode = {SEQ_COLUMNS:"sequence",STRUCTURE_COLUMNS:"structure_metrics"}.get(header,"observation")
        records = []
        for number, cells in enumerate(iterator, 2):
            if not any(cells):
                continue
            if len(cells) != len(header):
                raise ValueError(f"Row {number}: wrong column count.")
            row = dict(zip(header, (v.strip() for v in cells)))
            try:
                if mode=="sequence":
                    item=record(row["candidate"],row["component"],row["kind"],row["sequence"])
                elif mode=="structure_metrics":
                    item=structural_value(row)
                else:
                    item=observation(row)
                records.append(item)
            except ValueError as error:
                raise ValueError(f"Row {number}: {error}") from error
        return mode, records
    finally:
        iterator.close()


def codon_positions(feature, residue):
    """Three 1-based source bases in coding order; the terminal stop has its own slot."""
    coding = feature.get("coding")
    if not coding or type(residue) is not int or not 1 <= residue <= last_codon(feature):
        return []
    offset = coding["frame_offset"] + 3 * (residue - 1)
    positions = []
    for start, end, strand in feature["parts"]:
        length = end - start + 1
        if offset >= length:
            offset -= length
            continue
        for i in range(offset, min(length, offset + 3 - len(positions))):
            positions.append(start + i if strand == 1 else end - i)
        if len(positions) == 3:
            return positions
        offset = 0
    return []


def residue_at(feature, dna_position):
    coding = feature.get("coding")
    if not coding or type(dna_position) is not int:
        return None
    before = 0
    for start, end, strand in feature["parts"]:
        if start <= dna_position <= end:
            offset = before + (dna_position-start if strand == 1 else end-dna_position) - coding["frame_offset"]
            number = offset // 3 + 1
            return number if 1 <= number <= last_codon(feature) else None
        before += end-start+1
    return None


def last_codon(feature):
    return len(feature["translation"]) + int(feature["coding"].get("terminal_stop", True))


def coding_context(component, feature_index, position, residue=None):
    features = component["features"]
    if type(feature_index) is not int or not 0 <= feature_index < len(features):
        raise ValueError("Select a CDS annotation.")
    feature = features[feature_index]
    if not feature.get("coding"):
        raise ValueError("No verified codon correspondence for this annotation.")
    last = last_codon(feature)
    selected = residue_at(feature, position) if residue is None else residue
    if residue is not None and (type(residue) is not int or not 1 <= residue <= last):
        raise ValueError("Position outside this CDS.")
    start = max(1, min((selected or 1)-8, last-16))
    rows = []
    for n in range(start, min(start+17, last+1)):
        bases = codon_positions(feature, n)
        codon = "".join(component["seq"][b-1] for b in bases)
        if feature["parts"][0][2] == -1:
            codon = complement(codon)
        aa = feature["translation"][n-1] if n <= len(feature["translation"]) else "*"
        rows.append(dict(index=n, aa=aa, codon=codon, bases=bases))
    return dict(selected=selected, rows=rows, last=last)


def read_feature(f, item):
    label = next((f.qualifiers[k][0] for k in ("label", "gene", "product") if f.qualifiers.get(k)), f.type)
    feat = dict(label=label, type=f.type, location=str(f.location), parts=[], translation=None, coding=None)
    if hasattr(f,"snapgene_direction"):
        feat["snapgene_direction"] = f.snapgene_direction
    if f.location is None:
        return feat
    for n,p in enumerate(f.location.parts):
        exact = type(p.start) is ExactPosition and type(p.end) is ExactPosition
        known_prefix = (f.type == "mat_peptide" and n == len(f.location.parts)-1
                        and ((p.strand == 1 and type(p.start) is ExactPosition and type(p.end) is AfterPosition)
                             or (p.strand == -1 and type(p.start) is BeforePosition and type(p.end) is ExactPosition)))
        if (p.ref or p.ref_db or not (exact or known_prefix)
                or not 0 <= int(p.start) < int(p.end) <= len(item)):
            return feat
        if known_prefix:
            feat["open_peptide_end"] = True
    feat["parts"] = [[int(p.start)+1, int(p.end), p.strand] for p in f.location.parts]
    if f.type == "mat_peptide":
        feat["ordered"] = getattr(f.location, "operator", "join") == "join"
        feat["qualifiers"] = {key:f.qualifiers[key] for key in ("product","protein_id","translation","inference","experiment","exception")
                              if key in f.qualifiers}
    if f.type != "CDS":
        return feat
    intervals = sorted((start,end) for start,end,_ in feat["parts"])
    if (getattr(f.location, "operator", "join") != "join" or f.location.strand not in (-1,1)
            or any(end >= next_start for (_,end),(next_start,_) in zip(intervals, intervals[1:]))
            or {"transl_except","exception","pseudo","pseudogene","ribosomal_slippage","trans_splicing","artificial_location"} & f.qualifiers.keys()):
        return feat
    try:
        frame = int(f.qualifiers.get("codon_start", ["1"])[0])-1
        table = int(f.qualifiers.get("transl_table", ["1"])[0])
        if any(len(f.qualifiers.get(k,[None])) != 1 for k in ("codon_start","transl_table","translation")):
            raise ValueError("Conflicting CDS qualifiers.")
        coding = dict(frame_offset=frame, table=table)
        try:
            protein = str(f.translate(item.seq, cds=True))
        except TranslationError:
            # A deposited V segment may end inside a codon, without a termination codon.
            source = f.qualifiers.get("translation", [""])[0]
            if not source or not f.qualifiers.get("protein_id") or not 0 <= frame <= 2:
                raise
            extracted = f.extract(item.seq)[frame:]
            coding_length = len(source)*3
            if not 0 <= len(extracted)-coding_length <= 2:
                raise
            protein = str(extracted[:coding_length].translate(table=table))
            if "*" in protein or protein != source:
                raise
            coding.update(terminal_stop=False, protein_id=f.qualifiers["protein_id"][0])
        if f.qualifiers.get("translation", [protein])[0] != protein:
            raise ValueError("Source translation differs from the calculated CDS.")
        feat.update(translation=protein, coding=coding)
    except (ValueError, IndexError, TypeError, KeyError, TranslationError) as exc:
        feat["translation_issue"] = str(exc)
    return feat


def peptide_offsets(cds_parts, peptide_parts):
    """Inclusive zero-based offsets on the spliced CDS, in translation order."""
    if not peptide_parts:
        return None
    segments = []
    offset = 0
    for low, high, strand in cds_parts:
        segments.append((low, high, strand, offset))
        offset += high-low+1
    first = previous = None
    for left, right, strand in peptide_parts:
        hits = [(low,high,offset) for low,high,s,offset in segments
                if strand in (1,-1) and s == strand and low <= left <= right <= high]
        if len(hits) != 1:
            return None
        low, high, offset = hits[0]
        start = offset + (left-low if strand == 1 else high-right)
        if previous is not None and start != previous+1:
            return None
        if first is None:
            first = start
        previous = start + right-left
    return first, previous


def associate_mature_regions(features):
    sources = [f for f in features if f["type"]=="CDS"]
    for cds in sources:
        cds["mature_regions"] = []
        cds["mature_fragments"] = []
    for index, feature in enumerate(features):
        if feature["type"] != "mat_peptide" or not feature.get("ordered"):
            continue
        qualifiers = feature["qualifiers"]
        if "exception" in qualifiers:
            continue
        owners = [(cds,offsets) for cds in sources
                  if (offsets := peptide_offsets(cds["parts"], feature["parts"])) is not None]
        if len(owners) != 1:
            continue
        cds, (start,end) = owners[0]
        if not cds.get("coding"):
            continue
        frame = cds["coding"]["frame_offset"]
        start, end = start-frame, end+1-frame
        partial = feature.get("open_peptide_end", False)
        if start < 0 or start%3 or (not partial and end%3) or end//3 > len(cds["translation"]) or end//3 <= start//3:
            continue
        peptide = cds["translation"][start//3:end//3]
        if qualifiers.get("translation",[peptide]) != [peptide]:
            continue
        bucket = "mature_fragments" if partial else "mature_regions"
        cds[bucket].append(dict(feature_index=index, start=start//3+1, end=end//3))


def snapgene_record(data):
    # Use the pinned Biopython packet readers for sequence, intervals and qualifiers.
    # Its feature reader assigns +1 to every direction other than a reverse arrow.
    reader = SnapGeneIO.SnapGeneIterator(io.BytesIO(data))
    record = SeqRecord(None)
    for kind,length,payload in reader.packets:
        handler = SnapGeneIO._packet_handlers.get(kind)
        if handler is None:
            continue
        start = len(record.features)
        directions = []
        if kind == 0x0A:
            with parseString(payload) as doc:
                directions = [SnapGeneIO._get_attribute_value(f,"directionality")
                              for f in doc.getElementsByTagName("Feature")]
        handler(length,payload,record)
        if kind == 0x0A:
            for feature,direction in zip(record.features[start:],directions,strict=True):
                feature.snapgene_direction = {"1":"forward","2":"reverse","3":"both"}.get(direction,"unspecified")
                if direction not in ("1","2"):
                    feature.location.strand = None
    if not record.seq:
        raise ValueError("No DNA packet in file.")
    return record


def annotated(data, ext, base):
    fmt = "snapgene" if ext == ".dna" else "genbank"
    handle = io.BytesIO(data) if ext == ".dna" else io.StringIO(data.decode("utf-8-sig"))
    records = []
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        source = [snapgene_record(data)] if ext == ".dna" else SeqIO.parse(handle, fmt)
        for item in source:
            if "DNA" not in item.annotations.get("molecule_type", "").upper():
                raise ValueError("This importer requires an annotated DNA record.")
            features = [read_feature(f, item) for f in item.features]
            associate_mature_regions(features)
            label = item.id if item.id not in ("<unknown id>", ".") else base
            records.append(record(label, base, "DNA", str(item.seq), features, item.annotations.get("topology")))
    return records


def parse_file(path, fasta_kind="AA"):
    if path.stat().st_size > LIMIT:
        raise ValueError("File exceeds 24 MiB.")
    data = path.read_bytes()
    if len(data) > LIMIT:
        raise ValueError("File exceeds 24 MiB.")
    ext = path.suffix.lower()
    if ext in {".csv", ".tsv", ".xlsx"}:
        mode, records = structured(data, ext)
    elif ext in {".gb", ".gbk", ".genbank", ".dna"}:
        mode, records = "sequence", annotated(data, ext, path.stem)
    elif ext in {".fa", ".faa", ".fna", ".fasta"}:
        text = data.decode("utf-8-sig")
        if not text.startswith(">"):
            raise ValueError("FASTA must begin with a record header.")
        mode = "sequence"
        records = [record(r.id, r.description, fasta_kind, str(r.seq))
                   for r in SeqIO.parse(io.StringIO(text), "fasta")]
    else:
        raise ValueError("Unsupported file type.")
    if not records:
        raise ValueError("No records found.")
    return dict(mode=mode, records=records, filename=path.name, sha=hashlib.sha256(data).hexdigest(), raw=data)


def measurement_input(content):
    if isinstance(content,dict):
        if set(content)!=set(MEASUREMENT_COLUMNS) or not all(isinstance(v,str) for v in content.values()):
            raise ValueError("Invalid measurement fields.")
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer,MEASUREMENT_COLUMNS,delimiter="\t")
        writer.writeheader()
        writer.writerow(content)
        text,filename = buffer.getvalue(),"Entered measurement.tsv"
    elif isinstance(content,str):
        text,filename = content,"Pasted measurements.tsv"
    else:
        raise ValueError("Provide a measurement table.")
    data = text.encode("utf-8")
    if len(data)>LIMIT:
        raise ValueError("Table exceeds 24 MiB.")
    mode,records = structured(data,".tsv")
    if mode!="observation" or not records:
        raise ValueError("Provide a measurement table with column headings and at least one data row.")
    return dict(mode=mode,records=records,filename=filename,sha=hashlib.sha256(data).hexdigest(),raw=data)
