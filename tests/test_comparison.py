import math

import pytest

from antibody_insight.comparison import pearson, series_values


@pytest.mark.parametrize(("x","y","expected"),[
    ([0,1,2],[1,3,2],0.5),
    ([1e300,2e300,3e300],[0,-1,-2],-1),
    ([3,3],[2,5],None),
    ([1],[9],None),
    ([],[],None),
])
def test_correlation_of_included_candidates(x,y,expected):
    value=pearson([dict(x=a,y=b) for a,b in zip(x,y)])
    if expected is None:
        assert value is None
    else:
        assert math.isclose(value,expected,abs_tol=1e-12)


def test_explicit_replicates_contribute_one_mean_and_unknown_remains_missing():
    context=dict(metric="Signal",unit="AU",kind="Measured",conditions="buffer",source="Worksheet",candidate="A")
    raw=[dict(context,value=v,statistic="Individual",replicate_set="group") for v in (0,2,4,None)]
    summary=[dict(context,value=2,origin="Calculated")]
    axis=["Signal","AU","Measured","buffer","Worksheet"]
    result,source=series_values(raw,summary,axis)
    assert result["A"]==[(2,"Calculated mean")] and [r["value"] for r in source]==[0,2,4,None]
    raw.append(dict(context,value=3,statistic="Individual",replicate_set=""))
    result,_=series_values(raw,summary,axis)
    assert len(result["A"])==2
    with pytest.raises(ValueError):
        series_values(raw,summary,["Signal","mg","Measured","buffer","Worksheet"])
