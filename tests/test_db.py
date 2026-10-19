from app import db


def test_failure_cascade_query_uses_exasol_safe_alias(monkeypatch):
    class Result:
        def fetchall(self):
            return [("customer_sync", 2, "daily_reporting", 4, 1, " -> daily_reporting")]

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

    assert rows[0][2] == "daily_reporting"
    assert "PIPELINE_DEPENDENCY_CASCADE dependency_path" in connection.query
    assert "PIPELINE_DEPENDENCY_CASCADE cascade" not in connection.query
    assert connection.closed is True
