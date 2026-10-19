from scripts.benchmark_databases import benchmark_duckdb, run_comparison


def test_duckdb_comparison_workload_is_reproducible():
    result = benchmark_duckdb(1000, 3)

    assert result["engine"] == "DuckDB"
    assert result["rows"] == 1000
    assert result["repetitions"] == 3
    assert len(result["query_latency_ms"]["samples"]) == 3
    assert result["query_latency_ms"]["median"] > 0


def test_comparison_can_run_duckdb_without_exasol():
    result = run_comparison([200], 1, {"duckdb"})

    assert result["row_counts"] == [200]
    assert [entry["engine"] for entry in result["results"]] == ["DuckDB"]
