"""Local desktop bridge. File access is scoped to the open project and native pickers."""
import json
import os
import sqlite3
from pathlib import Path
from threading import Lock, RLock
from uuid import uuid4

import webview

from . import imports, project, structures

BASE = Path(__file__).resolve().parent
EXAMPLES = BASE.parent / "examples"


class Desktop:
    def __init__(self, initial=None):
        self._path = Path(initial) if initial else None
        self._session = uuid4().hex
        self._pending = None
        self._inspected = None
        self._lock = RLock()
        self._alignment_lock = Lock()
        self._alignment = None
        self._comparison = None
        self._comparison_version = 0

    def _check(self, session):
        if self._path is None or session != self._session:
            raise ValueError("Open the project again.")

    def _choose(self, save, types, name=""):
        result = webview.windows[0].create_file_dialog(
            webview.FileDialog.SAVE if save else webview.FileDialog.OPEN, file_types=types, save_filename=name)
        if not result:
            return None
        return Path(result if isinstance(result,str) else result[0])

    def current(self):
        with self._lock:
            if self._path is None:
                return None
            return dict(project.summary(self._path), session=self._session)

    def open_project(self, mode):
        if mode not in {"open","new","example"}:
            raise ValueError("Unknown project action.")
        file = self._choose(mode != "open", ("Antibody Insight project (*.ais)",),
                            "Synthetic example.ais" if mode == "example" else "Research project.ais")
        if file is None:
            return None
        if mode != "open":
            project.create_project(file)
            if mode == "example":
                from .example import populate
                populate(file)
        project.summary(file)
        with self._lock:
            self._session = uuid4().hex
            self._path, self._pending, self._inspected, self._alignment = file, None, None, None
            self._comparison = None
            return self.current()

    def inspect(self, session, key):
        with self._lock:
            self._check(session)
            detail = project.component_detail(self._path,key)
            self._inspected = detail
            return detail

    def codons(self, session, component, feature, position, residue=None):
        with self._lock:
            self._check(session)
            if self._inspected is None or self._inspected["id"] != component:
                self._inspected = project.component_detail(self._path,component)
            return imports.coding_context(self._inspected,feature,position,residue)

    def protein_targets(self, session, dna_id, feature_index):
        with self._lock:
            self._check(session)
            dna = project.component_detail(self._path, dna_id)
            if type(feature_index) is not int or not 0 <= feature_index < len(dna["features"]):
                raise ValueError("Select a CDS annotation.")
            feature = dna["features"][feature_index]
            if dna["kind"] != "DNA" or not feature.get("coding"):
                return []
            regions = [(None,1,len(feature["translation"]))]
            regions.extend((r["feature_index"],r["start"],r["end"]) for r in feature.get("mature_regions",[]))
            matches = []
            with project.connection(self._path) as db:
                for region, start, end in regions:
                    sequence = feature["translation"][start-1:end]
                    candidates = db.execute("""SELECT id,label FROM component WHERE candidate=? AND kind='AA'
                                               AND seq=? ORDER BY rowid""",(dna["candidate"],sequence))
                    matches.extend(dict(dict(r),region=region,start=start,end=end) for r in candidates)
            return matches

    def align(self, session, query, reference):
        from .alignment import align_pair
        key = (session,query,reference)
        with self._lock:
            self._check(session)
            if self._alignment and self._alignment[0] == key:
                return self._alignment[1]
            with project.connection(self._path) as db:
                rows = {r["id"]:r for r in db.execute("SELECT id,seq,kind FROM component WHERE id IN (?,?)",(query,reference))}
            if len(rows)!=2 or rows[query]["kind"] != rows[reference]["kind"]:
                raise ValueError("Select two distinct components of the same alphabet.")
        if not self._alignment_lock.acquire(blocking=False):
            raise ValueError("An alignment is running. Try again when it finishes.")
        try:
            result = align_pair(rows[query]["seq"],rows[reference]["seq"],rows[query]["kind"])
            with self._lock:
                self._check(session)
                self._alignment = (key,result)
            return result
        finally:
            self._alignment_lock.release()

    def coordinates(self, session, component, key):
        with self._lock:
            self._check(session)
            with project.connection(self._path) as db:
                row = db.execute("SELECT display_pdb,chain,mapping,filename,origin,hash FROM structure WHERE component=? AND id=?",
                                 (component,key)).fetchone()
                if row is None:
                    raise ValueError("The selected coordinates are unavailable.")
                mapping = json.loads(row["mapping"])
                if isinstance(mapping, dict):
                    positions = mapping["positions"]
                elif mapping:
                    raw = db.execute("SELECT bytes FROM source WHERE hash=?", (row["hash"],)).fetchone()[0]
                    detail = project.component_detail(self._path,component)
                    checked = structures.parse_coordinates(raw,row["filename"],detail)
                    positions = checked["mappings"].get(row["chain"],[])
                else:
                    positions = []
                return dict(dict(row), mapping=positions)

    def overlay(self,session,component,fixed_key,moving_component,moving_key,bounds=None):
        from .alignment import align_pair
        if fixed_key==moving_key:
            raise ValueError("Choose two different structures.")
        with self._lock:
            self._check(session)
            fixed=self.coordinates(session,component,fixed_key)
            moving=self.coordinates(session,moving_component,moving_key)
            with project.connection(self._path) as db:
                rows={r["id"]:r for r in db.execute("SELECT id,seq,kind FROM component WHERE id IN (?,?)",
                                                  (component,moving_component))}
        a,b=rows[component],rows[moving_component]
        if a["kind"]!="AA" or b["kind"]!="AA":
            raise ValueError("Superposition requires registered protein sequences.")
        if a["seq"]==b["seq"]:
            columns=[[i,i] for i in range(1,len(a["seq"])+1)]
        else:
            aligned=align_pair(a["seq"],b["seq"],"AA")
            if not aligned["unique"]:
                raise ValueError("Multiple optimal alignments prevent an unambiguous structure comparison.")
            columns=[pair for pair in aligned["columns"] if None not in pair]
        fit_columns=columns
        if bounds is not None:
            if (not isinstance(bounds,list) or len(bounds)!=2 or any(type(n) is not int for n in bounds)
                    or not 1<=bounds[0]<=bounds[1]<=len(a["seq"])):
                raise ValueError("Fit range must use valid positions on the displayed sequence.")
            fit_columns=[(i,j) for i,j in columns if bounds[0]<=i<=bounds[1]]
        result=structures.superpose(fixed,moving,fit_columns)
        with self._lock:
            self._check(session)
        return dict(result,moving=moving,correspondence=columns,fit_positions=len(fit_columns),bounds=bounds)

    def model_catalog(self,session):
        with self._lock:
            self._check(session)
            with project.connection(self._path) as db:
                return [dict(r) for r in db.execute(
                    "SELECT id,component,filename,chain,origin FROM structure WHERE chain<>'' ORDER BY rowid")]

    def numbered_domains(self,session,component):
        from .numbering import domains
        with self._lock:
            self._check(session)
            with project.connection(self._path) as db:
                row=db.execute("SELECT kind,seq FROM component WHERE id=?",(component,)).fetchone()
        if row is None or row["kind"]!="AA":
            raise ValueError("Select a registered amino acid sequence.")
        if len(row["seq"])>20000:
            raise ValueError("Numbering supports records of up to 20,000 amino acids.")
        value=domains(row["seq"])
        with self._lock:
            self._check(session)
        return value

    def compare_domains(self,session,choices):
        from .numbering import comparison
        if not isinstance(choices,list) or len(choices)<2:
            raise ValueError("Select two or more variable domains.")
        rows=[]
        seen=set()
        for choice in choices:
            component,idx=choice["component"],choice["domain"]
            if (not isinstance(component,str) or type(idx) is not int or idx<0
                    or (component,idx) in seen):
                raise ValueError("Choose distinct domains from registered proteins.")
            seen.add((component,idx))
            result=self.numbered_domains(session,component)["domains"]
            if idx>=len(result):
                raise ValueError("A selected domain is unavailable.")
            rows.append(result[idx])
        return comparison(rows)

    def structure_values(self,session,component,key):
        with self._lock:
            self._check(session)
            with project.connection(self._path) as db:
                if db.execute("SELECT 1 FROM structure WHERE id=? AND component=?",(key,component)).fetchone() is None:
                    raise ValueError("The selected coordinates are unavailable.")
                return project.structure_metrics(db,"WHERE s.id=? ORDER BY m.rowid",key)

    def select_representative(self,session,component,key):
        with self._lock:
            self._check(session)
            project.set_representative(self._path,component,key)
            self._comparison = None
            self._comparison_version += 1
            return self.current()

    def preview(self, session, kind, component=None, structure=None):
        with self._lock:
            self._check(session)
            self._pending = None
        if kind == "Structure":
            path = self._choose(False, ("Coordinates (*.pdb;*.cif;*.mmcif)",))
        else:
            path = self._choose(False, ("Sequence or table (*.fa;*.faa;*.fna;*.fasta;*.dna;*.gb;*.gbk;*.genbank;*.csv;*.tsv;*.xlsx)",))
        if path is None:
            return None
        if kind == "Structure":
            packet = structures.preview(path, self.inspect(session, component))
            packet["mode"] = "structure"
            output = dict(chains=list(packet["mappings"]), source_chains=packet["chains"])
        else:
            packet = imports.parse_file(path, kind)
            if packet["mode"] == "sequence":
                output = dict(records=[dict(candidate=r["candidate"], component=r["component"],
                            kind=r["kind"], size=len(r["sequence"]), features=len(r["features"]),
                            sequence=r["sequence"], annotations=[{
                                "label":f["label"], "type":f["type"], "parts":f["parts"],
                                "translation":f.get("translation"), "issue":f.get("translation_issue"),
                                "coding":f.get("coding"),"snapgene_direction":f.get("snapgene_direction")
                            } for f in r["features"]]) for r in packet["records"]])
            else:
                output = dict(records=packet["records"])
            if packet["mode"]=="structure_metrics":
                target=self.coordinates(session,component,structure)
                packet["structure"]=structure
                output["target"]=dict(filename=target["filename"],chain=target["chain"],origin=target["origin"])
        return self._preview_result(session,packet,output)

    def preview_measurements(self, session, content):
        with self._lock:
            self._check(session)
            self._pending = None
        packet = imports.measurement_input(content)
        return self._preview_result(session,packet,dict(records=packet["records"]))

    def _preview_result(self,session,packet,output):
        with self._lock:
            self._check(session)
            token = uuid4().hex
            self._pending = (token,packet)
            return dict(output, token=token, filename=packet["filename"], mode=packet["mode"])

    def accept(self, session, token, options):
        with self._lock:
            self._check(session)
            if not self._pending or self._pending[0] != token:
                raise ValueError("Preview the source again.")
            packet = self._pending[1]
            try:
                if packet["mode"] == "structure":
                    structures.save(self._path,packet,options.get("chain"),options["origin"])
                elif packet["mode"] == "structure_metrics":
                    project.commit_structure_metrics(self._path,packet,packet["structure"])
                else:
                    bindings = options.get("bindings")
                    if bindings is not None and len(bindings) != len(packet["records"]):
                        raise ValueError("Every record needs a confirmed assignment.")
                    project.commit(self._path,packet,bindings)
            except sqlite3.IntegrityError as error:
                raise ValueError("A component label or imported observation already exists. No rows were saved.") from error
            self._pending = None
            self._comparison = None
            self._comparison_version += 1
            return self.current()

    def compare_metrics(self,session,x_axis,y_axis):
        from .comparison import compare
        with self._lock:
            self._check(session)
            path=self._path
            self._comparison_version+=1
            version=self._comparison_version
        result=compare(path,x_axis,y_axis)
        with self._lock:
            self._check(session)
            token=uuid4().hex
            if version==self._comparison_version:
                self._comparison=token,result
            return dict(token=token,**{k:v for k,v in result.items() if k!="records"})

    def export_comparison(self,session,token):
        from .comparison import workbook
        with self._lock:
            self._check(session)
            if not self._comparison or self._comparison[0]!=token:
                raise ValueError("Reopen the comparison before exporting.")
            result=self._comparison[1]
        dest=self._choose(True,("Excel workbook (*.xlsx)",),"Candidate comparison.xlsx")
        if dest is None:
            return False
        data=workbook(result)
        return self._write_export(session,dest,data,{".xlsx"})

    def export_plot(self,session,image):
        return self._write_image(session,image,"Plot.png")

    def export_structure_image(self,session,image):
        return self._write_image(session,image,"Structure.png")

    def _write_image(self,session,image,name):
        import base64
        with self._lock:
            self._check(session)
        prefix="data:image/png;base64,"
        if not isinstance(image,str) or len(image)>32*1024*1024 or not image.startswith(prefix):
            raise ValueError("The image is unavailable.")
        data=base64.b64decode(image[len(prefix):],validate=True)
        if not data.startswith(b"\x89PNG\r\n\x1a\n") or data[-8:-4]!=b"IEND":
            raise ValueError("Invalid plot image.")
        dest=self._choose(True,("PNG image (*.png)",),name)
        return dest is not None and self._write_export(session,dest,data,{".png"})

    def save_view(self, session, state):
        with self._lock:
            self._check(session)
            with project.connection(self._path) as db:
                db.execute("INSERT OR REPLACE INTO meta VALUES('view',?)",(json.dumps(state,allow_nan=False),))
            return True

    def bookmarks(self,session):
        with self._lock:
            self._check(session)
            return project.bookmark_names(self._path)

    def add_bookmark(self,session,name,state):
        with self._lock:
            self._check(session)
            project.add_bookmark(self._path,name,state)
            return project.bookmark_names(self._path)

    def open_bookmark(self,session,name):
        with self._lock:
            self._check(session)
            project.restore_bookmark(self._path,name)
            return self.current()

    def export_fasta(self, session, keys):
        with self._lock:
            self._check(session)
            data = project.fasta(self._path,keys)
        return self._write_fasta(session,data,"sequences.fasta")

    def export_peptide(self, session, component, feature, region):
        with self._lock:
            self._check(session)
            data = project.mature_fasta(self._path, component, feature, region)
        return self._write_fasta(session,data,"mature-peptide.fasta")

    def _write_fasta(self, session, data, name):
        dest = self._choose(True, ("FASTA (*.fasta)",), name)
        if dest is None:
            return False
        return self._write_export(session,dest,data.encode("utf-8"),{".fa",".fasta",".fna",".faa"})

    def _write_export(self,session,dest,data,suffixes):
        with self._lock:
            self._check(session)
            if dest.suffix.lower() not in suffixes or dest.resolve() == self._path.resolve():
                raise ValueError("Choose a filename with a supported export extension.")
            import tempfile
            with tempfile.NamedTemporaryFile(dir=dest.parent,delete=False) as f:
                temp = Path(f.name)
            try:
                temp.write_bytes(data)
                os.replace(temp,dest)
            finally:
                temp.unlink(missing_ok=True)
        return True


def launch(initial=None):
    window = webview.create_window("Antibody Insight",(BASE/"ui/index.html").as_uri(),
                                   js_api=Desktop(initial),width=1250,height=830,min_size=(800,580))
    webview.start(gui="edgechromium" if os.name == "nt" else None, private_mode=True)
