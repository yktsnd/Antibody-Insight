import json
import struct

from antibody_insight import imports, project


def test_unstranded_cds_is_not_translated_and_legacy_display_is_corrected(tmp_path):
    def packet(kind,data):
        return struct.pack(">BI",kind,len(data))+data

    xml = b"""<Features>
    <Feature name="Unspecified" type="CDS"><Segment range="1-9"/></Feature>
    <Feature name="Both" type="misc_feature" directionality="3"><Segment range="1-6"/></Feature>
    <Feature name="Reverse" type="misc_feature" directionality="2"><Segment range="1-3"/></Feature>
    <Feature name="Forward" type="CDS" directionality="1"><Segment range="1-9"/></Feature>
    </Features>"""
    f = tmp_path/"Source.dna"
    f.write_bytes(packet(9,b"SnapGene"+struct.pack(">HHH",1,1,1))
                  +packet(0,b"\x00ATGGCTTAA")+packet(10,xml))
    db = tmp_path/"Annotations.ais"
    project.create_project(db)
    project.commit(db,imports.parse_file(f))
    key = project.summary(db)["components"][0]["id"]
    features = project.component_detail(db,key)["features"]
    assert [f["parts"][0][2] for f in features] == [None,None,-1,1]
    assert [f["snapgene_direction"] for f in features]==["unspecified","both","reverse","forward"]
    assert features[0]["translation"] is None and features[3]["translation"]=="MA"
    previous = json.loads(json.dumps(features))
    for old in previous:
        old.pop("snapgene_direction")
    previous[0]["translation"],previous[0]["parts"][0][2] = "MA",1
    with project.connection(db) as conn:
        conn.execute("UPDATE component SET features=? WHERE id=?",(json.dumps(previous),key))
    assert project.component_detail(db,key)["features"] == features
