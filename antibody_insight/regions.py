"""Reference-anchored comparison of declared sequence regions."""
from collections import Counter, defaultdict
from io import BytesIO

from Bio.Seq import complement

from .alignment import align_pair

MAX_ROWS = 64
MAX_CELLS = 1_000_000
MAX_PAIRWORK = 24_000_000
MAX_REGION_LENGTH = 20_000


def describe_region(detail, choice):
    reference = detail["seq"]
    feature_index = choice.get("feature")
    if feature_index is None:
        start, end = choice.get("start"), choice.get("end")
        if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(reference):
            raise ValueError("Enter a valid inclusive sequence range.")
        if end-start+1>MAX_REGION_LENGTH:
            raise ValueError("Choose a region of at most 20,000 letters.")
        offsets = list(range(start,end+1))
        letters = reference[start-1:end]
        label = f"{start}–{end}"
        parts = [[start,end,1]]
    else:
        if type(feature_index) is not int or not 0 <= feature_index < len(detail["features"]):
            raise ValueError("The selected annotation is unavailable.")
        feature = detail["features"][feature_index]
        parts = feature["parts"]
        if (not parts or feature.get("open_peptide_end") or feature.get("location","").startswith("order{")
                or any(not 1<=start<=end<=len(reference) or strand not in (-1,1)
                       for start,end,strand in parts)):
            raise ValueError("Choose an annotation with exact coordinates and a single known direction.")
        strand=parts[0][2]
        if any(part[2]!=strand for part in parts) or (strand==-1 and detail["kind"]!="DNA"):
            raise ValueError("Choose an annotation with a single supported direction.")
        if sum(end-start+1 for start,end,_ in parts)>MAX_REGION_LENGTH:
            raise ValueError("Choose a region of at most 20,000 letters.")
        spans = [range(start,end+1) if strand==1 else range(end,start-1,-1) for start,end,_ in parts]
        offsets = [p for span in spans for p in span]
        if len(set(offsets))!=len(offsets):
            raise ValueError("The selected annotation has overlapping intervals.")
        letters = "".join(reference[p-1] for p in offsets)
        if strand==-1:
            letters = complement(letters)
        label = feature["label"]+" · "+feature["type"]
    parsed=dict(component=detail["id"],candidate=detail["candidate"],label=label,kind=detail["kind"],
                component_label=detail.get("label"),source=detail.get("filename"),source_hash=detail.get("hash"),
                letters=letters,offsets=offsets,parts=parts)
    if detail["kind"]=="DNA":
        counts=Counter(letters)
        parsed["gc"]=[counts["G"]+counts["C"],sum(counts[b] for b in "ACGT")]
    return parsed


def compare_regions(regions):
    if not 2 <= len(regions) <= MAX_ROWS:
        raise ValueError(f"Choose two to {MAX_ROWS} regions.")
    anchor,*others=regions
    if any(r["kind"]!=anchor["kind"] for r in others):
        raise ValueError("Compare DNA with DNA or protein with protein.")
    ref=anchor["letters"]
    if sum(len(ref)*len(row["letters"]) for row in others if row["letters"]!=ref)>MAX_PAIRWORK:
        raise ValueError("These regions exceed the alignment work limit. Select smaller ranges.")
    width=len(ref)
    anchored=[[list(range(1,width+1)),True]]
    insertions=defaultdict(dict)
    method=""
    for row_number,row in enumerate(others,1):
        result=align_pair(ref,row["letters"],anchor["kind"])
        method=result["method"]
        slots=[None]*width
        last=0
        for first,second in result["columns"]:
            if first is None:
                insertions[last].setdefault(row_number,[]).append(second)
            else:
                last=first
                slots[first-1]=second
        anchored.append([slots,result["unique"]])

    blocks={}
    for position,entries in insertions.items():
        grouped=defaultdict(dict)
        for row,positions in entries.items():
            inserted="".join(regions[row]["letters"][p-1] for p in positions)
            grouped[inserted][row]=positions
        blocks[position]=grouped

    def unanchored(position):
        # Coincident insertions with identical observed letters share a block. Distinct
        # insertions have no defensible cross-row ordering or column correspondence.
        for inserted,group in blocks.get(position,{}).items():
            for j in range(len(inserted)):
                yield [group[i][j] if i in group else None for i in range(len(regions))]

    total=width+sum(len(inserted) for groups in blocks.values() for inserted in groups)
    if total*len(regions)>MAX_CELLS:
        raise ValueError("These regions exceed one million displayed cells. Select smaller ranges.")
    columns=[]
    insertion_columns=[]
    for base in range(width+1):
        if base:
            columns.append([slots[base-1] for slots,_ in anchored])
            insertion_columns.append(False)
        for col in unanchored(base):
            columns.append(col)
            insertion_columns.append(True)

    known=set("ACGT" if anchor["kind"]=="DNA" else "ACDEFGHIKLMNOPQRSTUVWY")
    identity=[]
    for first,left in enumerate(regions):
        stats=[]
        for second,right in enumerate(regions):
            if first!=second and not (anchored[first][1] and anchored[second][1]):
                stats.append(None)
                continue
            paired=matches=0
            for col,floating in zip(columns,insertion_columns):
                a,b=col[first],col[second]
                if (not floating or first==second) and a is not None and b is not None:
                    letter_a,letter_b=left["letters"][a-1],right["letters"][b-1]
                    if letter_a not in known or letter_b not in known:
                        continue
                    paired+=1
                    matches+=letter_a==letter_b
            stats.append([matches,paired])
        identity.append(stats)
    rows=[]
    for row,(_,unique) in zip(regions,anchored):
        rows.append(dict(row,unique=unique))
    consensus=[]
    for col,floating in zip(columns,insertion_columns):
        symbols=[r["letters"][n-1] for r,n in zip(rows,col) if r["unique"] and n is not None] if not floating else []
        counts=Counter(letter for letter in symbols if letter in known)
        lead=counts.most_common(1)
        consensus.append(lead[0][0] if lead and lead[0][1]*2>len(symbols) else None)
    return dict(columns=columns,rows=rows,identity=identity,consensus=consensus,method="Reference-anchored · "+method,
                insertions=insertion_columns)


def workbook(result):
    from openpyxl import Workbook
    from openpyxl.cell import WriteOnlyCell

    book=Workbook(write_only=True)

    def append(sheet,values):
        cells=[]
        for v in values:
            cell=WriteOnlyCell(sheet,value=v)
            if isinstance(v,str):
                cell.data_type="s"
            cells.append(cell)
        sheet.append(cells)

    sheet=book.create_sheet("Regions")
    append(sheet,["Method",result["method"]])
    append(sheet,["Identity","Equal known letters divided by paired known letters at reference positions. "
                            "Cross-region identity omits unanchored insertions and tied alignments."])
    append(sheet,["Row","Candidate ID","Component ID","Component","Region","Source file","Source SHA-256","Unique anchor"])
    for index,row in enumerate(result["rows"],1):
        append(sheet,[index,*[row[k] for k in ("candidate","component","component_label","label","source","source_hash","unique")]])
    matrix=book.create_sheet("Identity")
    append(matrix,["First region","Second region","Matches","Paired","Identity"])
    for i,stats in enumerate(result["identity"],1):
        for j,pair in enumerate(stats,1):
            matched,paired=pair if pair else (None,None)
            append(matrix,[i,j,matched,paired,matched/paired if paired else None])
    columns=book.create_sheet("Source coordinates")
    append(columns,["Alignment column","Region","Letter","Original position","Strand","Unanchored insertion","Consensus"])
    for index,(col,insertion,consensus) in enumerate(zip(result["columns"],result["insertions"],result["consensus"]),1):
        for row_id,(position,row) in enumerate(zip(col,result["rows"]),1):
            letter,origin=(None,None) if position is None else (row["letters"][position-1],row["offsets"][position-1])
            append(columns,[index,row_id,letter,origin,row["parts"][0][2],insertion,consensus])
    output=BytesIO()
    book.save(output)
    return output.getvalue()
