from scripts.setup_database import load_statements


def test_sql_loader_ignores_comments_and_splits_statements(tmp_path):
    sql_file = tmp_path / "sample.sql"
    sql_file.write_text("-- comment\nSELECT 1;\nSELECT 2;\n")

    assert load_statements(sql_file) == ["SELECT 1", "SELECT 2"]


def test_reset_recreates_schema_seed_and_analytics(monkeypatch, capsys):
    from scripts import setup_database

    class Result:
        def fetchone(self):
            return (1,)

    class Connection:
        def __init__(self):
            self.queries = []
            self.closed = False

        def execute(self, query):
            self.queries.append(query.strip())
            return Result()

        def close(self):
            self.closed = True

    connection = Connection()
    monkeypatch.setattr(setup_database, "get_connection", lambda: connection)
    monkeypatch.setattr("sys.argv", ["setup_database", "--reset"])

    setup_database.main()

    all_sql = "\n".join(connection.queries)
    assert "DROP SCHEMA OPSINTEL CASCADE" in all_sql
    assert "CREATE TABLE OPSINTEL.PIPELINE_RUNS" in all_sql
    assert "INSERT INTO OPSINTEL.PIPELINE_RUNS" in all_sql
    assert "CREATE OR REPLACE VIEW OPSINTEL.PIPELINE_HEALTH_FEATURES" in all_sql
    assert connection.closed is True
    assert "reset successfully" in capsys.readouterr().out
