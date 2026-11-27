from io import BytesIO
import sqlite3

import pytest
from openpyxl import load_workbook

from antibody_insight import comparison, example, imports, project, structures


def test_structure_values_remain_scoped_to_candidate_region_and_source(tmp_path):
    db=tmp_path/"Project.ais"
    project.create_project(db)
    example.populate(db)
    base=project.summary(db)
    component=base["state"]["component"]
    available=project.component_detail(db,component)
    fixed=available["structures"][0]["id"]
    with project.connection(db) as conn:
        raw,coordinate_hash=conn.execute("""SELECT b.bytes,b.hash FROM structure s JOIN source b ON b.hash=s.hash
                                             WHERE s.id=?""",(fixed,)).fetchone()
    other=next(r["id"] for r in base["components"] if r["candidate"]!=available["candidate"] and r["kind"]=="AA")
    packet=structures.parse_coordinates(raw,"Second.pdb",project.component_detail(db,other))
    structures.save(db,packet,"A","Experimental")
    second=project.component_detail(db,other)["structures"][0]["id"]
    with pytest.raises(ValueError,match="belonging"):
        project.set_representative(db,component,second)

    table=tmp_path/"external.csv"
    table.write_text("metric,value,unit,region,conditions,source\n"
                     "Demo,0,AU,Entire chain,Condition,Calculator\n"
                     "Demo,7,AU,Residue 2,Condition,Calculator\n")
    metric=imports.parse_file(table)
    project.commit_structure_metrics(db,metric,fixed)
    with pytest.raises(sqlite3.IntegrityError):
        project.commit_structure_metrics(db,metric,fixed)
    assert project.summary(db)["observations"]==base["observations"]
    project.set_representative(db,component,fixed)
    measures=[r for r in project.summary(db)["observations"] if r["kind"]=="Structure computed"]
    assert [(r["region"],r["value"]) for r in measures]==[("Entire chain",0),("Residue 2",7)]
    assert all(r["coordinate_hash"]==coordinate_hash and r["structure_id"]==fixed for r in measures)

    x=["Demo","AU","Structure computed","Condition","Calculator","Residue 2"]
    raw_data=base["observations"][0]
    y=[raw_data[k] for k in comparison.FIELDS]
    result=comparison.compare(db,x,y)
    assert result["n"]==1 and result["pairs"][0]["x"]==7 and result["r"] is None
    book=load_workbook(BytesIO(comparison.workbook(result)),read_only=True)
    try:
        header,measurement,*_=list(book["Source records"].values)
        values=dict(zip(header,measurement))
        assert values["Region"]=="Residue 2" and values["Structure ID"]==fixed
        assert values["Coordinate SHA-256"]==coordinate_hash and values["SHA-256"]==metric["sha"]
    finally:
        book.close()
