"""SQLite project operations. Each modifying action is one local transaction."""
import json
import sqlite3
import math
import statistics
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

SCHEMA = """
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE source(hash TEXT PRIMARY KEY, bytes BLOB NOT NULL);
CREATE TABLE candidate(id TEXT PRIMARY KEY, label TEXT UNIQUE NOT NULL);
CREATE TABLE component(id TEXT PRIMARY KEY, candidate TEXT NOT NULL REFERENCES candidate,
 label TEXT NOT NULL, kind TEXT NOT NULL, seq TEXT NOT NULL, features TEXT NOT NULL,
 topology TEXT, hash TEXT NOT NULL REFERENCES source, filename TEXT NOT NULL, imported TEXT NOT NULL,
 UNIQUE(candidate,label));
CREATE TABLE observation(id TEXT PRIMARY KEY, candidate TEXT NOT NULL REFERENCES candidate,
 metric TEXT NOT NULL, value REAL, unit TEXT NOT NULL, kind TEXT NOT NULL, sample TEXT NOT NULL,
 conditions TEXT NOT NULL, source TEXT NOT NULL, event_time TEXT NOT NULL,
 hash TEXT NOT NULL REFERENCES source, filename TEXT NOT NULL, imported TEXT NOT NULL, row_no INTEGER NOT NULL,
 UNIQUE(hash,row_no));
CREATE TABLE structure(id TEXT PRIMARY KEY, component TEXT NOT NULL REFERENCES component,
 filename TEXT NOT NULL, hash TEXT NOT NULL REFERENCES source, imported TEXT NOT NULL,
 chain TEXT NOT NULL, origin TEXT NOT NULL, display_pdb TEXT NOT NULL, mapping TEXT NOT NULL);
CREATE INDEX by_component ON structure(component);
INSERT INTO meta VALUES('format','antibody-insight-project/1');
"""
def uid():
    return uuid4().hex


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection(path, create=False):
    mode = "rwc" if create else "rw"
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=" + mode, uri=True)
    try:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA trusted_schema=OFF")
        with db:
            yield db
    finally:
        db.close()


def create_project(path):
    path = Path(path)
    with path.open("xb"):
        pass
    try:
        with connection(path, create=True) as db:
            db.executescript("BEGIN;\n" + SCHEMA)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


MEASUREMENT_SCHEMA = """CREATE TABLE IF NOT EXISTS measurement_detail(
 observation TEXT PRIMARY KEY REFERENCES observation(id), replicate_set TEXT NOT NULL,
 statistic TEXT NOT NULL, error_type TEXT NOT NULL, error REAL, n INTEGER)"""
REPRESENTATIVE_SCHEMA = """CREATE TABLE IF NOT EXISTS representative(
 candidate TEXT PRIMARY KEY REFERENCES candidate(id), structure_id TEXT NOT NULL REFERENCES structure(id))"""
STRUCTURE_METRIC_SCHEMA = """CREATE TABLE IF NOT EXISTS structure_metric(
 id TEXT PRIMARY KEY, structure_id TEXT NOT NULL REFERENCES structure(id), metric TEXT NOT NULL,
 value REAL NOT NULL, unit TEXT NOT NULL, region TEXT NOT NULL, conditions TEXT NOT NULL,
 source TEXT NOT NULL, hash TEXT NOT NULL REFERENCES source(hash), filename TEXT NOT NULL,
 imported TEXT NOT NULL, row_no INTEGER NOT NULL, UNIQUE(structure_id,metric,unit,region,conditions,source))"""


def has_table(db,name):
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None


def saved_view(db):
    return json.loads(db.execute("SELECT coalesce((SELECT value FROM meta WHERE key='view'),'{}')").fetchone()[0])


def bookmark_names(path):
    with connection(path) as db:
        if not has_table(db,"bookmark"):
            return []
        return [r[0] for r in db.execute("SELECT name FROM bookmark ORDER BY rowid")]


def add_bookmark(path,name,state):
    if not isinstance(name,str) or not (name:=name.strip()) or len(name)>100:
        raise ValueError("Enter a bookmark name of 1 to 100 characters.")
    if not isinstance(state,dict):
        raise ValueError("The observation is unavailable.")
    snapshot={k:v for k,v in state.items() if k!="note"}
    with connection(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS bookmark(name TEXT PRIMARY KEY, state TEXT NOT NULL)")
        try:
            db.execute("INSERT INTO bookmark VALUES(?,?)",(name,json.dumps(snapshot,allow_nan=False)))
        except sqlite3.IntegrityError as exc:
            raise ValueError("A bookmark with this name already exists.") from exc


def restore_bookmark(path,name):
    with connection(path) as db:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("SELECT state FROM bookmark WHERE name=?",(name,)).fetchone() if has_table(db,"bookmark") else None
        if row is None:
            raise ValueError("The bookmark is unavailable.")
        state=json.loads(row[0])
        state["note"]=saved_view(db).get("note","")
        db.execute("INSERT OR REPLACE INTO meta VALUES('view',?)",(json.dumps(state,allow_nan=False),))


def representatives(db):
    if not has_table(db,"representative"):
        return {}
    return dict(db.execute("""SELECT r.candidate,r.structure_id FROM representative r
        JOIN structure s ON s.id=r.structure_id JOIN component c ON c.id=s.component AND c.candidate=r.candidate""").fetchall())


def set_representative(path,component,structure):
    with connection(path) as db:
        row=db.execute("""SELECT c.candidate FROM component c JOIN structure s ON s.component=c.id
                          WHERE c.id=? AND s.id=?""",(component,structure)).fetchone()
        if row is None:
            raise ValueError("Select a coordinate file belonging to the active component.")
        db.execute(REPRESENTATIVE_SCHEMA)
        db.execute("INSERT OR REPLACE INTO representative VALUES(?,?)",(row[0],structure))


def commit_structure_metrics(path,packet,structure):
    with connection(path) as db:
        db.execute("BEGIN")
        if not db.execute("SELECT 1 FROM structure WHERE id=?",(structure,)).fetchone():
            raise ValueError("The selected structure is unavailable.")
        db.execute(STRUCTURE_METRIC_SCHEMA)
        db.execute("INSERT OR IGNORE INTO source VALUES(?,?)",(packet["sha"],packet["raw"]))
        stamp=now()
        for i,r in enumerate(packet["records"],1):
            db.execute("INSERT INTO structure_metric VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                       (uid(),structure,*[r[k] for k in ("metric","value","unit","region","conditions","source")],
                        packet["sha"],packet["filename"],stamp,i))


def structure_metrics(db,where,value=None):
    if not has_table(db,"structure_metric"):
        return []
    rows=db.execute("""SELECT m.*,s.chain,s.origin AS coordinate_origin,s.hash AS coordinate_hash,
        s.filename AS coordinate_file,c.candidate,c.label AS coordinate_component
        FROM structure_metric m JOIN structure s ON s.id=m.structure_id JOIN component c ON c.id=s.component """
        +where,() if value is None else (value,))
    return [dict(row) for row in rows]


def measurements(db):
    fields = "o.id,o.candidate,o.metric,o.value,o.unit,o.kind,o.sample,o.conditions,o.source,o.event_time,o.filename,o.row_no,o.hash,o.imported"
    has_details = has_table(db,"measurement_detail")
    if has_details:
        query = f"""SELECT {fields},coalesce(d.statistic,'Individual') AS statistic,
                    coalesce(d.replicate_set,'') AS replicate_set,d.error_type,d.error,d.n
                    FROM observation o LEFT JOIN measurement_detail d ON o.id=d.observation ORDER BY o.rowid"""
    else:
        query = f"""SELECT {fields},'Individual' AS statistic,'' AS replicate_set,
                    NULL AS error_type,NULL AS error,NULL AS n FROM observation o ORDER BY o.rowid"""
    rows = [dict(row) for row in db.execute(query)]
    summaries = []
    groups = defaultdict(list)
    attributes = ("candidate","metric","unit","kind","conditions","source","replicate_set")
    for row in rows:
        context = {field:row[field] for field in attributes}
        if row["statistic"] == "Mean":
            summaries.append(dict(context, origin="Reported",value=row["value"],n=row["n"],
                                  sd=row["error"] if row["error_type"]=="SD" else None,
                                  sem=row["error"] if row["error_type"]=="SEM" else None,
                                  readings=[row["id"]]))
        elif row["replicate_set"]:
            groups[tuple(context.values())].append(row)
    for identity, members in groups.items():
        values = [r["value"] for r in members if r["value"] is not None]
        n = len(values)
        sd = sem = None
        if n>1:
            try:
                sd = statistics.stdev(values)
                sem = sd/math.sqrt(n)
            except OverflowError:
                scale = max(map(abs,values))
                sem = (statistics.stdev(v/scale for v in values)/math.sqrt(n))*scale
        summaries.append(dict(zip(attributes,identity),origin="Calculated",
                              value=statistics.mean(values) if n else None, n=n, sd=sd,
                              sem=sem,
                              readings=[r["id"] for r in members]))
    if has_table(db,"representative"):
        rows.extend(dict(r,kind="Structure computed",statistic="Individual",
                         sample=r["coordinate_file"]+" · chain "+r["chain"],event_time="",
                         replicate_set="",error_type=None,error=None,n=None)
                    for r in structure_metrics(db,"JOIN representative p ON p.structure_id=s.id AND p.candidate=c.candidate ORDER BY m.rowid"))
    return rows,summaries


def summary(path):
    with connection(path) as db:
        db.execute("BEGIN")
        if db.execute("SELECT value FROM meta WHERE key='format'").fetchone()[0] != "antibody-insight-project/1":
            raise ValueError("Unknown project format.")
        observations, summaries = measurements(db)
        return dict(title=Path(path).stem,
                    candidates=[dict(r) for r in db.execute("SELECT id,label FROM candidate ORDER BY rowid")],
                    components=[dict(r) for r in db.execute("SELECT id,candidate,label,kind,length(seq) AS size FROM component ORDER BY rowid")],
                    observations=observations,summaries=summaries,representatives=representatives(db),
                    state=saved_view(db))


def commit(path, packet, bindings=None):
    if packet["mode"] not in {"sequence","observation"}:
        raise ValueError("Choose the record target before saving.")
    stamp = now()
    with connection(path) as db:
        db.execute("INSERT OR IGNORE INTO source VALUES(?,?)", (packet["sha"],packet["raw"]))
        for i, item in enumerate(packet["records"]):
            identity = bindings[i] if bindings is not None else item
            key = identity["candidate"].strip()
            if not key:
                raise ValueError("Candidate key is required.")
            entry = db.execute("SELECT id FROM candidate WHERE label=?", (key,)).fetchone()
            if entry:
                candidate = entry[0]
            elif packet["mode"] == "sequence":
                candidate = uid()
                db.execute("INSERT INTO candidate VALUES(?,?)", (candidate,key))
            else:
                raise ValueError(f"Unknown candidate key: {key}")
            if packet["mode"] == "sequence":
                component = identity["component"].strip()
                if not component:
                    raise ValueError("Component label is required.")
                db.execute("INSERT INTO component VALUES(?,?,?,?,?,?,?,?,?,?)",
                           (uid(),candidate,component,item["kind"],item["sequence"],json.dumps(item["features"]),
                            item["topology"],packet["sha"],packet["filename"],stamp))
            else:
                fields = [item[k] for k in ("metric","value","unit","kind","sample","conditions","source","event_time")]
                observation_id = uid()
                db.execute("INSERT INTO observation VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (observation_id,candidate,*fields,packet["sha"],packet["filename"],stamp,i+1))
                if "statistic" in item:
                    if i == 0:
                        db.execute(MEASUREMENT_SCHEMA)
                    db.execute("INSERT INTO measurement_detail VALUES(?,?,?,?,?,?)",
                               (observation_id,item["replicate_set"],item["statistic"],item["error_type"],item["error"],item["n"]))


def component_detail(path, key):
    with connection(path) as db:
        row = db.execute("SELECT * FROM component WHERE id=?", (key,)).fetchone()
        if row is None:
            raise ValueError("Component is unavailable.")
        detail = dict(row)
        detail["features"] = json.loads(detail["features"])
        snapgene = Path(detail["filename"]).suffix.lower()==".dna"
        legacy_direction = snapgene and any(f["type"]!="primer_bind" and "snapgene_direction" not in f for f in detail["features"])
        if legacy_direction or any(f["type"] == "CDS" and ("coding" not in f or "mature_fragments" not in f) for f in detail["features"]):
            from .imports import annotated
            filename = Path(detail["filename"])
            raw = db.execute("SELECT bytes FROM source WHERE hash=?", (detail["hash"],)).fetchone()
            if raw and filename.suffix.lower() in {".dna", ".gb", ".gbk", ".genbank"}:
                def signature(features):
                    return [(f["type"], f["label"], f["location"]) for f in features]
                matches = [r["features"] for r in annotated(raw[0], filename.suffix.lower(), filename.stem)
                           if r["sequence"] == detail["seq"] and (snapgene or signature(r["features"]) == signature(detail["features"]))]
                if matches and all(result == matches[0] for result in matches):
                    detail["features"] = matches[0]
        detail["structures"] = [dict(r) for r in db.execute(
            "SELECT id,filename,chain,origin FROM structure WHERE component=? ORDER BY rowid", (key,))]
        return detail


def fasta(path, keys):
    if not keys:
        raise ValueError("Select a component to export.")
    lines = []
    with connection(path) as db:
        for key in dict.fromkeys(keys):
            r = db.execute("""SELECT c.*, a.label AS owner FROM component c
                              JOIN candidate a ON a.id=c.candidate WHERE c.id=?""", (key,)).fetchone()
            if r is None:
                raise ValueError("Selected component is unavailable.")
            lines.append(f">{r['id']} candidate={quote(r['owner'],safe='')} component={quote(r['label'],safe='')} type={r['kind']}")
            lines.extend(r["seq"][i:i+80] for i in range(0,len(r["seq"]),80))
    return "\n".join(lines)+"\n"


def mature_fasta(path, key, feature_index, region_index):
    detail = component_detail(path,key)
    if type(feature_index) is not int or not 0 <= feature_index < len(detail["features"]):
        raise ValueError("Select a CDS annotation.")
    cds = detail["features"][feature_index]
    if type(region_index) is not int or not cds.get("coding"):
        raise ValueError("A source-annotated mature peptide is required.")
    region = next((r for r in cds.get("mature_regions",[]) if r["feature_index"]==region_index),None)
    if not region:
        raise ValueError("No exact mature-peptide correspondence for this CDS.")
    start,end = region["start"],region["end"]
    sequence = cds["translation"][start-1:end]
    feature = detail["features"][region_index]
    with connection(path) as db:
        owner = db.execute("SELECT label FROM candidate WHERE id=?", (detail["candidate"],)).fetchone()[0]
    header = (f">{key}.cds{feature_index+1}.mat{region_index+1} type=AA feature=mat_peptide "
              f"candidate={quote(owner,safe='')} component={quote(detail['label'],safe='')} "
              f"label={quote(feature['label'],safe='')} translation_positions={start}-{end} source_sha256={detail['hash']}")
    return header+"\n"+"\n".join(sequence[i:i+80] for i in range(0,len(sequence),80))+"\n"
