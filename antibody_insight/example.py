from pathlib import Path
from . import imports, project, structures


def populate(path):
    examples = Path(__file__).resolve().parent.parent / "examples"
    for name in ("sequences.csv","observations.csv"):
        project.commit(path, imports.parse_file(examples / name))
    plasmid = imports.parse_file(examples / "coordinate-example.gb")
    project.commit(path, plasmid, [{"candidate":"Example A","component":"Example plasmid"}])
    processing = imports.parse_file(examples / "processing-example.gb")
    project.commit(path, processing, [{"candidate":"Example A","component":"Annotated precursor"}])
    view = project.summary(path)
    owner = next(c["id"] for c in view["candidates"] if c["label"] == "Example A")
    component = next(c["id"] for c in view["components"] if c["candidate"] == owner and c["kind"] == "AA")
    packet = structures.preview(examples / "synthetic-peptide.pdb",project.component_detail(path,component))
    structures.save(path, packet,"A","Unknown")
    import json
    with project.connection(path) as db:
        db.execute("INSERT INTO meta VALUES('view',?)", (json.dumps(dict(component=component,
            note="Synthetic demonstration. The short sequences, coordinates and observations are invented for software testing.")),))
