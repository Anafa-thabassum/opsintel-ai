from scripts.exasol_proof import fetch_proof


def test_exasol_proof_returns_history_and_evidence(monkeypatch):
    from scripts import exasol_proof

    class Result:
        def __init__(self, rows):
            self.rows = rows

        def fetchall(self):
            return self.rows

    class Connection:
        closed = False

        def execute(self, query, parameters):
            if "PIPELINE_HEALTH_FEATURES" in query:
                assert parameters == {"pipeline_name": "daily_sales_import"}
                return Result([
                    (1, "FAILED", 100, 80, 20, 80, "SUCCESS", 96, 20, "now")
                ])
            assert parameters == {"run_id": 1}
            return Result([
                (1, "daily_sales_import", "FAILED", 100, 80, 3, "ERROR", "ended early", "now")
            ])

        def close(self):
            self.closed = True

    connection = Connection()
    monkeypatch.setattr(exasol_proof, "get_connection", lambda: connection)

    result = fetch_proof()

    assert result["source"] == "live Exasol query"
    assert result["historical_completeness_rows"][0][5] == 80
    assert result["evidence_rows"][0][5] == 3
    assert connection.closed is True
