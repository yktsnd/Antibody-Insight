"""Local IMGT numbering with verified correspondence to registered sequence positions."""
import re
from math import isfinite

from immunum import Annotator, __version__, regions_for

SCHEMES={"imgt":"IMGT","kabat":"Kabat"}


def position_key(label,scheme="imgt"):
    match=re.fullmatch(r"([1-9][0-9]{0,2})(?:\.([1-9][0-9]*)|([A-Z]+))?",label)
    if match is None:
        raise ValueError("The annotation contains an unsupported IMGT position.")
    base=int(match[1])
    insertion=int(match[2] or 0)
    for char in match[3] or "":
        insertion=insertion*26+ord(char)-64
    centers=(32,33,60,61,111,112)
    if base>128 or (scheme=="imgt" and insertion and base not in centers):
        raise ValueError("The annotation contains an unsupported IMGT position.")
    return base, -insertion if scheme=="imgt" and base in (33,61,112) else insertion


def region_of(label,scheme="imgt",chain="H"):
    base,_=position_key(label,scheme)
    return next(region.upper() for region,(start,end) in regions_for(scheme,chain).items() if start<=base<=end)


def complete_imgt(domain):
    anchors=domain.numbering
    end="128" if domain.chain=="H" else "127"
    return (next(iter(anchors))=="1" and next(reversed(anchors))==end
            and anchors.get("23")=="C" and anchors.get("104")=="C" and anchors.get("118") in {"F","W"})


def domains(sequence,scheme="imgt"):
    if scheme not in SCHEMES:
        raise ValueError("Choose IMGT or Kabat numbering.")
    chains=["H","K","L"]
    standard=[d for d in Annotator(chains=chains,scheme="imgt").number_domains(sequence)
              if d.numbering and d.chain in chains and d.confidence is not None]
    verified={(d.chain,d.query_start,d.query_end):complete_imgt(d) for d in standard}
    numbered=standard if scheme=="imgt" else Annotator(chains=chains,scheme=scheme).number_domains(sequence)
    mapped=[]
    last=0
    for domain in numbered:
        if not domain.numbering or domain.chain not in ("H","K","L") or domain.confidence is None:
            continue
        start,stop=domain.query_start,domain.query_end+1
        assignments=sorted(domain.numbering.items(),key=lambda p:position_key(p[0],scheme))
        if (not last<=start<stop<=len(sequence) or
                "".join(aa for _,aa in assignments)!=sequence[start:stop]):
            raise ValueError("The numbered residues could not be verified against the registered sequence.")
        last=stop
        complete=verified.get((domain.chain,domain.query_start,domain.query_end),False)
        entries=[]
        for i,(label,aa) in enumerate(assignments,1):
            base,insertion=position_key(label,scheme)
            display=f"{base}.{abs(insertion)}" if scheme=="imgt" and insertion else label
            entries.append(dict(label=display,aa=aa,position=start+i,region=region_of(display,scheme,domain.chain)))
        if not isfinite(domain.confidence):
            raise ValueError("The numbering engine did not return a finite score.")
        mapped.append(dict(chain=domain.chain,scheme=scheme,score=domain.confidence,complete=complete,
                           start=start+1,end=stop,residues=entries))
    return dict(method="Immunum "+__version__+" · "+SCHEMES[scheme]+" · computed",domains=mapped)


def comparison(domain_rows):
    if len(domain_rows)<2 or any(not row["complete"] for row in domain_rows):
        raise ValueError("Compare at least two domains with supported end positions and anchors.")
    if len({row["chain"] for row in domain_rows})!=1:
        raise ValueError("Choose domains with the same assigned chain type.")
    schemes={row.get("scheme","imgt") for row in domain_rows}
    if len(schemes)!=1:
        raise ValueError("Choose a single numbering scheme.")
    scheme=schemes.pop()
    labels=sorted({r["label"] for row in domain_rows for r in row["residues"]},key=lambda p:position_key(p,scheme))
    by_position=[{r["label"]:r for r in row["residues"]} for row in domain_rows]
    return [dict(label=p,region=region_of(p,scheme,domain_rows[0]["chain"]),
                 residues=[row.get(p) for row in by_position]) for p in labels]
