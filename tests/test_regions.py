import pytest

from antibody_insight.regions import compare_regions, describe_region


def region(letters,kind="DNA"):
    detail=dict(id="component",candidate="candidate",kind=kind,seq=letters,features=[])
    return describe_region(detail,dict(start=1,end=len(letters)))


def test_reverse_join_keeps_each_coordinate_and_oriented_base():
    detail=dict(id="component",candidate="candidate",kind="DNA",seq="TTAACCCGCCAT",
                features=[dict(label="GOI",type="CDS",parts=[[8,12,-1],[1,4,-1]])])
    observed=describe_region(detail,dict(feature=0))
    assert observed["letters"]=="ATGGCTTAA"
    assert observed["offsets"]==[12,11,10,9,8,4,3,2,1]
    assert observed["gc"]==[3,9]
    detail["features"][0]["parts"]=[[8,12,-1],[1,9,-1]]
    with pytest.raises(ValueError,match="overlapping"):
        describe_region(detail,dict(feature=0))


def test_distinct_insertions_are_not_counted_as_cross_region_pairs():
    regions=[region(s) for s in ("ATGGCTTAA","ATGGCTGTCTAA","ATGGCTAAATAA","ATGGCTGTCTAA")]
    result=compare_regions(regions)
    assert result["identity"][1][2]==[9,9]
    assert result["identity"][1][1]==[12,12]
    assert [column[1:] for column,inserted in zip(result["columns"],result["insertions"]) if inserted]==[
        [7,None,7],[8,None,8],[9,None,9],[None,7,None],[None,8,None],[None,9,None]]
    assert "".join(result["consensus"][i] or "" for i in range(len(result["columns"])))=="ATGGCTTAA"
    for index,row in enumerate(regions):
        assert [column[index] for column in result["columns"] if column[index]]==list(range(1,len(row["letters"])+1))


def test_ties_and_unknown_letters_do_not_enter_identity():
    tied=compare_regions([region("AAAA"),region("AAA")])
    assert tied["identity"][0][1] is None and not tied["rows"][1]["unique"]
    unknown=compare_regions([region("ANGT"),region("ANGT")])
    assert unknown["identity"][0][1]==[3,3] and unknown["consensus"]==["A",None,"G","T"]
    with pytest.raises(ValueError,match="DNA with DNA"):
        compare_regions([region("AGCT"),region("MA","AA")])


def test_protein_comparison_tracks_substitution_after_an_insertion():
    result=compare_regions([region(s,"AA") for s in ("MKTW","MKATW","MKSW")])
    assert result["identity"][0]==[[4,4],[4,4],[3,4]]
    assert result["columns"][2]==[None,3,None]
    assert result["columns"][3]==[3,4,3]
