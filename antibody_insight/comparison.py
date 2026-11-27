"""Candidate-level comparisons of two explicitly selected observation series."""
import io
import math
import statistics
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell

from . import project

FIELDS=("metric","unit","kind","conditions","source")


def series_values(records,summaries,axis):
    if not isinstance(axis,list) or len(axis) not in {len(FIELDS),len(FIELDS)+1} or not all(isinstance(v,str) for v in axis):
        raise ValueError("Choose a project metric for each axis.")
    def matches(row):
        fields=[row[k] for k in FIELDS]
        if row.get("region"):
            fields.append(row["region"])
        return fields==axis
    rows=[r for r in records if matches(r)]
    if not rows:
        raise ValueError("The selected measurement series is unavailable.")
    by_candidate=defaultdict(list)
    for summary in summaries:
        if matches(summary) and summary["value"] is not None:
            by_candidate[summary["candidate"]].append((summary["value"],summary["origin"]+" mean"))
    for row in rows:
        if row["statistic"]=="Individual" and not row["replicate_set"] and row["value"] is not None:
            by_candidate[row["candidate"]].append((row["value"],"Single record"))
    return by_candidate,rows


def pearson(points):
    if len(points)<2:
        return None
    axes=[]
    for field in ("x","y"):
        values=[p[field] for p in points]
        if min(values)==max(values):
            return None
        # Scaling by a power of two preserves significant bits at large magnitudes.
        exponent=math.frexp(max(map(abs,values)))[1]
        axes.append([math.ldexp(v,-exponent) for v in values])
    try:
        return statistics.correlation(*axes)
    except statistics.StatisticsError:
        return None


def compare(path,x_axis,y_axis):
    if x_axis==y_axis:
        raise ValueError("Choose two different metric series.")
    with project.connection(path) as db:
        db.execute("BEGIN")
        rows,summaries=project.measurements(db)
        candidates=list(db.execute("SELECT id,label FROM candidate ORDER BY rowid"))
    x,x_rows=series_values(rows,summaries,x_axis)
    y,y_rows=series_values(rows,summaries,y_axis)
    pairs=[]
    for candidate,label in candidates:
        pair=dict(candidate=candidate,label=label)
        for axis,values in (("x",x[candidate]),("y",y[candidate])):
            value,status=values[0] if len(values)==1 else (None,"Multiple values" if values else "Missing")
            pair[axis]=value
            pair[axis+"_basis"]=status
        pair["included"]=pair["x"] is not None and pair["y"] is not None
        pairs.append(pair)
    points=[p for p in pairs if p["included"]]
    return dict(x_axis=x_axis,y_axis=y_axis,pairs=pairs,n=len(points),r=pearson(points),
                records={"x":x_rows,"y":y_rows})


def workbook(result):
    record_count=sum(map(len,result["records"].values()))
    if max(record_count,len(result["pairs"]))>=1048576:
        raise ValueError("The comparison exceeds Excel's row limit.")
    for rows in (result["pairs"],*result["records"].values()):
        if any(isinstance(v,str) and len(v)>32767 for row in rows for v in row.values()):
            raise ValueError("A text field exceeds Excel's cell limit.")
    book=Workbook(write_only=True)
    def append(sheet,values):
        # User-provided text remains literal even when a spreadsheet reads formulas.
        row=[]
        for value in values:
            cell=WriteOnlyCell(sheet,value=value)
            if isinstance(value,str):
                cell.data_type="s"
            row.append(cell)
        sheet.append(row)
    method=book.create_sheet("Comparison")
    append(method,["Axis",*FIELDS,"Region"])
    for axis in ("x","y"):
        append(method,[axis.upper(),*result[axis+"_axis"]])
    append(method,["Unit of comparison","Candidate"])
    append(method,["Included candidates",result["n"]])
    append(method,["Pearson r",result["r"]])
    append(method,["Pairing rule","One numeric mean or single ungrouped record per candidate and axis. Missing or ambiguous values are excluded."])
    pairs=book.create_sheet("Candidates")
    append(pairs,["Candidate ID","Candidate","X","X basis","Y","Y basis","Included"])
    for p in result["pairs"]:
        append(pairs,[p[k] for k in ("candidate","label","x","x_basis","y","y_basis","included")])
    records=book.create_sheet("Source records")
    keys=("id","candidate",*FIELDS,"value","statistic","sample","replicate_set","error_type","error","n",
          "event_time","filename","row_no","region","structure_id","coordinate_component","chain","coordinate_origin",
          "coordinate_hash","hash","imported")
    append(records,["Axis","Record ID","Candidate ID","Metric","Unit","Kind","Conditions","Source","Value",
                    "Statistic","Sample","Replicate set","Error type","Error","n","Event time","File","Record ordinal",
                    "Region","Structure ID","Component","Author chain","Coordinate origin","Coordinate SHA-256","SHA-256","Imported at"])
    for axis,rows in result["records"].items():
        for row in rows:
            append(records,[axis.upper(),*[row.get(k) for k in keys]])
    output=io.BytesIO()
    book.save(output)
    return output.getvalue()
