import pytest

from antibody_insight.numbering import comparison, domains, position_key, region_of


def test_imgt_cdr3_labels_follow_the_published_sequence_order():
    labels=["111","112","111.1","112.1","112.2","111.2","110","113"]
    assert sorted(labels,key=position_key)==["110","111","111.1","111.2","112.2","112.1","112","113"]
    assert all(region_of(label)=="CDR3" for label in labels)
    assert region_of("118")=="FR4"
    with pytest.raises(ValueError):
        position_key("104.1")


def test_missing_label_does_not_shift_following_correspondence():
    def row(labels):
        return dict(chain="H",complete=True,residues=[
            dict(label=k,aa=v,position=i+1) for i,(k,v) in enumerate(labels)])
    columns=comparison([row([("111","A"),("112","Y")]),row([("111","A"),("111.1","G"),("112","F")])])
    assert columns[1]["residues"][0] is None
    assert [r["position"] for r in columns[-1]["residues"]]==[2,3]
    with pytest.raises(ValueError,match="same assigned chain"):
        comparison([row([("111","A")]),dict(row([("111","A")]),chain="K")])


def test_short_peptide_gets_no_variable_domain():
    assert domains("MA")["domains"]==[]
