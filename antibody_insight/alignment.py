"""Pairwise record correspondence. All positions exposed to the UI are 1-based."""
from Bio import __version__ as biopython_version
from Bio.Align import PairwiseAligner

from .imports import sequence


def align_pair(query, reference, kind):
    query = sequence(query,kind)
    reference = sequence(reference,kind)
    if max(len(query),len(reference)) > 20000:
        raise ValueError("Whole-record alignment supports up to 20,000 letters per record.")
    if query == reference:
        columns = [[n,n] for n in range(1,len(query)+1)]
        unique, score = True, 2*len(query)
    else:
        if len(query)*len(reference) > 4_000_000:
            raise ValueError("These records exceed the whole-record alignment budget of four million position pairs.")
        aligner = PairwiseAligner(mode="global",match_score=2,mismatch_score=-1,open_gap_score=-5,extend_gap_score=-1)
        paths = aligner.align(query,reference)
        best = next(paths)
        score = best.score
        unique = next(paths,None) is None
        columns = [[int(a)+1 if a>=0 else None,int(b)+1 if b>=0 else None] for a,b in best.indices.T]
    pairs = [(a,b) for a,b in columns if a is not None and b is not None]
    matches = sum(query[a-1] == reference[b-1] for a,b in pairs)
    return dict(columns=columns,matches=matches,paired=len(pairs),unique=unique,score=score,
                method=f"Biopython {biopython_version} · global · match +2 · mismatch −1 · gap open −5 · extend −1")
