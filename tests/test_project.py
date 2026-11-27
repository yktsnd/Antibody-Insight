import io
import struct
from pathlib import Path

import pytest
from openpyxl import Workbook
from antibody_insight import example, imports, project, structures

DATA = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def case(tmp_path):
    p=tmp_path/"Synthetic.ais"
    project.create_project(p)
    example.populate(p)
    return p


def test_source_and_duplicate_sequences(case):
    overview=project.summary(case)
    peptides=[r for r in overview["components"] if r["kind"]=="AA"]
    out=project.fasta(case,[r["id"] for r in peptides]).splitlines()
    assert out[1]==out[3]=="MA"
    assert out[0]!=out[2]
    assert all(r["id"] in header for r,header in zip(peptides,out[::2]))
    assert "seq" not in peptides[0]
    detail=project.component_detail(case,peptides[0]["id"])
    with project.connection(case) as db:
        assert db.execute("SELECT bytes FROM source WHERE hash=?",(detail["hash"],)).fetchone()[0]==(DATA/"sequences.csv").read_bytes()


def test_transaction_rollback(case,tmp_path):
    before=project.summary(case)
    text="candidate,component,kind,sequence\nOther,First,AA,K\nExample A,Peptide,AA,MA\n"
    f=tmp_path/"batch.csv";f.write_text(text)
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        project.commit(case,imports.parse_file(f))
    assert project.summary(case)==before


def test_source_mapping(case):
    overview=project.summary(case);key=overview["state"]["component"]
    detail=project.component_detail(case,key)
    p=structures.preview(DATA/"synthetic-peptide.pdb",detail)
    assert p["mappings"]=={"A":[[10,""],[10,"A"]]}
    assert structures.preview(DATA/"synthetic-peptide.pdb",dict(detail,seq="AA"))["mappings"]=={}
    with pytest.raises(ValueError):
        structures.save(case,p,"X","Unknown")


def test_missing_and_zero(case,tmp_path):
    file=tmp_path/"measurements.csv"
    text=(DATA/"observations.csv").read_text().replace(",12.5,",",,")
    file.write_text(text)
    records=imports.parse_file(file)
    assert [r["value"] for r in records["records"]]==[0,None]
    records["records"][1]["candidate"]="Absent"
    with pytest.raises(ValueError,match="Unknown candidate"):
        project.commit(case,records)
    assert len(project.summary(case)["observations"])==2


def test_xlsx_values_and_formula(tmp_path):
    path=tmp_path/"sequence.xlsx"; wb=Workbook();s=wb.active
    s.append(imports.SEQ_COLUMNS);s.append(["Example","Part","DNA","ACGT"]);wb.save(path)
    assert imports.parse_file(path)["records"][0]["sequence"]=="ACGT"
    s["D2"]='="ACGT"';wb.save(path)
    with pytest.raises(ValueError,match="formulas"):
        imports.parse_file(path)


def test_snapgene_binary(tmp_path):
    def packet(t,data):return struct.pack(">BI",t,len(data))+data
    path=tmp_path/"synthetic.dna"
    path.write_bytes(packet(9,b"SnapGene"+struct.pack(">HHH",1,1,1))+packet(0,b"\x01ATGGCTTAA"))
    r=imports.parse_file(path)["records"][0]
    assert (r["kind"],r["topology"],r["sequence"])==("DNA","circular","ATGGCTTAA")
    path.write_bytes(b"not a SnapGene file")
    with pytest.raises((ValueError,EOFError)):imports.parse_file(path)


def test_reverse_strand_cds(tmp_path):
    from Bio import SeqIO
    from Bio.Seq import Seq
    from Bio.SeqRecord import SeqRecord
    from Bio.SeqFeature import SeqFeature,SimpleLocation
    path=tmp_path/"reverse.gb"
    r=SeqRecord(Seq("TTAAGCCAT"),id="Synthetic",annotations={"molecule_type":"DNA"})
    r.features=[SeqFeature(SimpleLocation(0,9,strand=-1),type="CDS",qualifiers={"translation":["MA"]})]
    SeqIO.write(r,path,"genbank")
    feature=imports.parse_file(path)["records"][0]["features"][0]
    assert feature["parts"]==[[1,9,-1]] and feature["translation"]=="MA"
    assert "translation_issue" not in feature


def test_export_unknown_rejected(case):
    with pytest.raises(ValueError):project.fasta(case,[])
    with pytest.raises(ValueError):project.fasta(case,["unknown"])


def test_existing_project_protected(case):
    with pytest.raises(FileExistsError):project.create_project(case)
    assert len(project.summary(case)["candidates"])==2
