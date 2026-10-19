from app import db


def test_failure_cascade_query_filters_stale_and_reversed_failures(monkeypatch):
    class Result:
        def fetchall(self):
            return [
                (
                    "customer_sync", 2, "2026-10-19 01:00:00",
                    "daily_reporting", 4, "2026-10-19 01:30:00",
                    1, " -> daily_reporting", 30,
                ),
                (
                    "customer_sync", 2, "2026-10-19 01:00:00",
                    "stale_report", 5, "2026-10-19 03:01:00",
                    1, " -> stale_report", 121,
                ),
                (
                    "customer_sync", 2, "2026-10-19 01:00:00",
                    "earlier_report", 6, "2026-10-19 00:55:00",
                    1, " -> earlier_report", -5,
                ),
                (
                    "customer_sync", 2, "2026-10-19 01:00:00",
                    "simultaneous_report", 7, "2026-10-19 01:00:00",
                    1, " -> simultaneous_report", 0,
                ),
            ]

    class Connection:
        def __init__(self):
            self.query = ""
            self.closed = False

        def execute(self, query):
            self.query = query
            return Result()

        def close(self):
            self.closed = True

    connection = Connection()
    monkeypatch.setattr(db, "get_connection", lambda: connection)

    rows = db.get_failure_cascades()

    assert [row[3] for row in rows] == ["daily_reporting"]
    assert rows[0][8] == 30
    assert "PIPELINE_DEPENDENCY_CASCADE dependency_path" in connection.query
    assert "PIPELINE_DEPENDENCY_CASCADE cascade" not in connection.query
    assert "MINUTES_BETWEEN(downstream.RUN_TIME, upstream.RUN_TIME)" in connection.query
    assert ") > 0" in connection.query
    assert ") <= 120" in connection.query
    assert connection.closed is True
