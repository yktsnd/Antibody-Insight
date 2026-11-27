"""Local IMGT numbering with verified correspondence to registered sequence positions."""
import re
from math import isfinite

from immunum import Annotator, __version__

REGIONS=(("FR1",26),("CDR1",38),("FR2",55),("CDR2",65),("FR3",104),("CDR3",117),("FR4",128))


def position_key(label):
    match=re.fullmatch(r"([1-9][0-9]{0,2})(?:\.([1-9][0-9]*))?",label)
    if match is None:
        raise ValueError("The annotation contains an unsupported IMGT position.")
    base=int(match[1])
    insertion=int(match[2] or 0)
    if base>128 or (insertion and base not in (111,112)):
        raise ValueError("The annotation contains an unsupported IMGT position.")
    return base, -insertion if base==112 else insertion


def region_of(label):
    base,_=position_key(label)
    return next(region for region,end in REGIONS if base<=end)


def domains(sequence):
    annotator=Annotator(chains=["H","K","L"],scheme="imgt")
    mapped=[]
    last=0
    for domain in annotator.number_domains(sequence):
        if not domain.numbering or domain.chain not in ("H","K","L") or domain.confidence is None:
            continue
        start,stop=domain.query_start,domain.query_end+1
        assignments=sorted(domain.numbering.items(),key=lambda p:position_key(p[0]))
        if (not last<=start<stop<=len(sequence) or
                "".join(aa for _,aa in assignments)!=sequence[start:stop]):
            raise ValueError("The numbered residues could not be verified against the registered sequence.")
        last=stop
        anchors=domain.numbering
        complete=(assignments[0][0]=="1" and assignments[-1][0]=="128"
                  and anchors.get("23")=="C" and anchors.get("104")=="C" and anchors.get("118") in {"F","W"})
        entries=[dict(label=label,aa=aa,position=start+i,region=region_of(label))
                 for i,(label,aa) in enumerate(assignments,1)]
        if not isfinite(domain.confidence):
            raise ValueError("The numbering engine did not return a finite score.")
        mapped.append(dict(chain=domain.chain,score=domain.confidence,complete=complete,
                           start=start+1,end=stop,residues=entries))
    return dict(method="Immunum "+__version__+" · IMGT · computed",domains=mapped)


def comparison(domain_rows):
    if len(domain_rows)<2 or any(not row["complete"] for row in domain_rows):
        raise ValueError("Compare at least two domains with supported end positions and anchors.")
    if len({row["chain"] for row in domain_rows})!=1:
        raise ValueError("Choose domains with the same assigned chain type.")
    labels=sorted({r["label"] for row in domain_rows for r in row["residues"]},key=position_key)
    by_position=[{r["label"]:r for r in row["residues"]} for row in domain_rows]
    return [dict(label=p,region=region_of(p),residues=[row.get(p) for row in by_position]) for p in labels]
