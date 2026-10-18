from datetime import datetime

from scripts.benchmark_exasol import make_rows, percentile


def test_benchmark_rows_are_deterministic_and_include_failures():
    rows = list(make_rows(20, datetime(2026, 1, 1)))

    assert len(rows) == 20
    assert rows[0][0:3] == (1, "pipeline_01", "SUCCESS")
    assert rows[-1][0:3] == (20, "pipeline_00", "FAILED")
    assert rows[-1][4] < rows[-1][3]


def test_percentile_uses_nearest_rank():
    assert percentile([4, 1, 3, 2], 0.95) == 4
