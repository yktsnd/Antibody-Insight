"""AC-09: hand-calculated summaries from explicitly grouped measurements."""

import csv
import math
import sqlite3

import pytest

from antibody_insight import imports, project


LEGACY_HEADER = (
    "candidate", "metric", "value", "unit", "kind", "sample",
    "conditions", "source", "event_time",
)
EXTENDED_HEADER = LEGACY_HEADER + (
    "replicate_set", "statistic", "error_type", "error", "n",
)


def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def create_project_with_candidate(tmp_path):
    path = tmp_path / "Measurements.ais"
    project.create_project(path)
    sequences = write_csv(
        tmp_path / "candidate.csv",
        ("candidate", "component", "kind", "sequence"),
        [("Alpha", "Synthetic chain", "AA", "MA")],
    )
    project.commit(path, imports.parse_file(sequences))
    return path


def find_summary(rows, metric, replicate_set, conditions):
    matches = [
        row for row in rows
        if row["metric"] == metric
        and row["replicate_set"] == replicate_set
        and row["conditions"] == conditions
    ]
    assert len(matches) == 1
    return matches[0]


def test_explicit_replicates_reported_means_and_legacy_rows(tmp_path):
    database = create_project_with_candidate(tmp_path)
    extended = write_csv(
        tmp_path / "extended.csv",
        EXTENDED_HEADER,
        [
            # Three measured replicates plus one missing replicate: mean=2,
            # sample SD=2, SEM=2/sqrt(3); blank value is preserved but excluded.
            ("Alpha", "Signal", "0", "a.u.", "Measured", "S1", "buffer=A", "assay", "",
             "signal-r1", "Individual", "", "", ""),
            ("Alpha", "Signal", "2", "a.u.", "Measured", "S2", "buffer=A", "assay", "",
             "signal-r1", "Individual", "", "", ""),
            ("Alpha", "Signal", "4", "a.u.", "Measured", "S3", "buffer=A", "assay", "",
             "signal-r1", "Individual", "", "", ""),
            ("Alpha", "Signal", "", "a.u.", "Measured", "S4", "buffer=A", "assay", "",
             "signal-r1", "Individual", "", "", ""),
            # A singleton has a mean but no estimable sample SD or SEM.
            ("Alpha", "Single", "7", "a.u.", "Measured", "S5", "buffer=A", "assay", "",
             "single-r1", "Individual", "", "", ""),
            # Same replicate-set label under distinct conditions stays separate.
            ("Alpha", "Activity", "1", "uM", "Measured", "S6", "pH=6", "assay", "",
             "conditioned", "Individual", "", "", ""),
            ("Alpha", "Activity", "3", "uM", "Measured", "S7", "pH=6", "assay", "",
             "conditioned", "Individual", "", "", ""),
            ("Alpha", "Activity", "100", "uM", "Measured", "S8", "pH=7", "assay", "",
             "conditioned", "Individual", "", "", ""),
            # An independent mean with unknown uncertainty and sample size.
            ("Alpha", "Reported unknown", "10", "mg/mL", "Measured", "lab mean", "day=1", "lab", "",
             "reported-unknown", "Mean", "", "", ""),
            # A supplied SEM is retained; with unknown n, no SD is inferred.
            ("Alpha", "Reported SEM", "12", "mg/mL", "Measured", "lab mean", "day=1", "lab", "",
             "reported-sem", "Mean", "SEM", "1.5", ""),
        ],
    )
    packet = imports.parse_file(extended)
    project.commit(database, packet)

    legacy = write_csv(
        tmp_path / "legacy.csv",
        LEGACY_HEADER,
        [
            ("Alpha", "Legacy", "2", "a.u.", "Measured", "L1", "same", "old assay", ""),
            ("Alpha", "Legacy", "3", "a.u.", "Measured", "L2", "same", "old assay", ""),
            ("Alpha", "Legacy", "4", "a.u.", "Measured", "L3", "same", "old assay", ""),
        ],
    )
    project.commit(database, imports.parse_file(legacy))

    result = project.summary(database)
    observations = result["observations"]
    summaries = result["summaries"]

    assert len(observations) == 13
    assert sum(row["value"] is None for row in observations) == 1
    assert sorted(row["value"] for row in observations if row["value"] is not None) == [
        0.0, 1.0, 2.0, 2.0, 3.0, 3.0, 4.0, 4.0, 7.0, 10.0, 12.0, 100.0
    ]
    assert len(summaries) == 6

    main = find_summary(summaries, "Signal", "signal-r1", "buffer=A")
    assert main["origin"] == "Calculated"
    assert main["candidate"] == result["candidates"][0]["id"]
    assert (main["metric"], main["unit"], main["conditions"], main["source"], main["replicate_set"]) == (
        "Signal", "a.u.", "buffer=A", "assay", "signal-r1"
    )
    assert main["value"] == pytest.approx(2.0)
    assert main["n"] == 3
    assert main["sd"] == pytest.approx(2.0)
    assert main["sem"] == pytest.approx(2.0 / math.sqrt(3))

    singleton = find_summary(summaries, "Single", "single-r1", "buffer=A")
    assert singleton["origin"] == "Calculated"
    assert singleton["value"] == 7.0
    assert singleton["n"] == 1
    assert singleton["sd"] is None
    assert singleton["sem"] is None

    conditioned_6 = find_summary(summaries, "Activity", "conditioned", "pH=6")
    assert conditioned_6["value"] == pytest.approx(2.0)
    assert conditioned_6["n"] == 2
    assert conditioned_6["sd"] == pytest.approx(math.sqrt(2))
    assert conditioned_6["sem"] == pytest.approx(1.0)
    conditioned_7 = find_summary(summaries, "Activity", "conditioned", "pH=7")
    assert conditioned_7["value"] == 100.0
    assert conditioned_7["n"] == 1
    assert conditioned_7["sd"] is None
    assert conditioned_7["sem"] is None

    unknown = find_summary(summaries, "Reported unknown", "reported-unknown", "day=1")
    assert unknown["origin"] == "Reported"
    assert unknown["value"] == 10.0
    assert unknown["n"] is None
    assert unknown["sd"] is None
    assert unknown["sem"] is None

    supplied_sem = find_summary(summaries, "Reported SEM", "reported-sem", "day=1")
    assert supplied_sem["origin"] == "Reported"
    assert supplied_sem["value"] == 12.0
    assert supplied_sem["n"] is None
    assert supplied_sem["sd"] is None
    assert supplied_sem["sem"] == pytest.approx(1.5)

    assert not any(row["metric"] == "Legacy" for row in summaries)

    before = result
    with pytest.raises(sqlite3.IntegrityError):
        project.commit(database, imports.parse_file(extended))
    assert project.summary(database) == before


@pytest.mark.parametrize(
    ("error_type", "error", "n"),
    [
        ("SD", "nan", "3"),
        ("SEM", "-0.5", "3"),
        ("", "", "2.5"),
    ],
)
def test_invalid_uncertainty_or_noninteger_sample_count_is_rejected(
    tmp_path, error_type, error, n
):
    path = write_csv(
        tmp_path / "invalid.csv",
        EXTENDED_HEADER,
        [
            ("Alpha", "Reported", "1", "a.u.", "Measured", "S1", "condition=x", "assay", "",
             "reported", "Mean", error_type, error, n),
        ],
    )

    with pytest.raises(ValueError):
        imports.parse_file(path)
