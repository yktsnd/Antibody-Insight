"""Evaluate an isolated Immunum installation with previously downloaded public fixtures."""
import argparse
import importlib.metadata
import json
import sys
from pathlib import Path

from Bio import SeqIO


def verify(public,installation,output):
    sys.path.insert(0,str(installation))
    from immunum import Annotator

    chains=[*SeqIO.parse(public/"1IGT.faa","fasta"),
            *(SeqIO.read(public/(p+".faa"),"fasta") for p in ("AAA58746.1","AAA58747.1"))]
    annotator=Annotator(chains=["H","K","L"],scheme="imgt")
    labels=("prefix","fr1","cdr1","fr2","cdr2","fr3","cdr3","fr4","postfix")
    tested=[]
    for record in chains:
        sequence=str(record.seq)
        numbering=annotator.number(sequence)
        regions=annotator.segment(sequence)
        parts=[getattr(regions,label) or "" for label in labels]
        tested.append(dict(record=record.id,length=len(sequence),scheme=str(numbering.scheme),
                           chain=str(numbering.chain),confidence=float(numbering.confidence),
                           segment_lengths=dict(zip(labels,map(len,parts))),
                           segments_reconstruct_input="".join(parts)==sequence))
    try:
        short=annotator.number("MA")
    except (ValueError,RuntimeError) as exc:
        negative=dict(status="Rejected",detail=str(exc))
    else:
        negative=dict(status="No assignment")
        if short is not None:
            negative.update(chain=short.chain,confidence=short.confidence,
                            numbered_positions=len(short.numbering or {}))
            if short.chain and short.confidence is not None and short.numbering:
                negative["status"]="Assigned"
    receipt=dict(version=importlib.metadata.version("immunum"),platform=sys.platform,cases=tested,negative=negative,
                 scope="Separate local Windows installation; reconstruction only, no independent numbering oracle")
    output.write_text(json.dumps(receipt,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("public",type=Path)
    parser.add_argument("installation",type=Path)
    parser.add_argument("output",type=Path)
    a=parser.parse_args()
    verify(a.public,a.installation,a.output)
