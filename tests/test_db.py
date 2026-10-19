from pathlib import Path
import ssl

import duckdb
import pytest

from app import db


def test_local_exasol_defaults_still_connect(monkeypatch):
    captured = {}
    connection = object()

    monkeypatch.setenv("EXASOL_PASSWORD", "local-test-password")
    monkeypatch.delenv("EXASOL_DSN", raising=False)
    monkeypatch.delenv("EXASOL_USER", raising=False)
    monkeypatch.delenv("EXASOL_TLS_VERIFY", raising=False)
    monkeypatch.setattr(
        db.pyexasol,
        "connect",
        lambda **kwargs: captured.update(kwargs) or connection,
    )

    assert db.get_connection() is connection
    assert captured["dsn"] == "127.0.0.1:8563"
    assert captured["user"] == "sys"
    assert captured["websocket_sslopt"]["cert_reqs"] == ssl.CERT_NONE


def test_remote_exasol_without_tls_verification_is_rejected(monkeypatch):
    attempted = False

    def connect(**kwargs):
        nonlocal attempted
        attempted = True

    monkeypatch.setenv("EXASOL_DSN", "db.example.com:8563")
    monkeypatch.setenv("EXASOL_PASSWORD", "remote-test-password")
    monkeypatch.setenv("EXASOL_TLS_VERIFY", "false")
    monkeypatch.setattr(db.pyexasol, "connect", connect)

    with pytest.raises(ValueError, match="requires EXASOL_TLS_VERIFY=true"):
        db.get_connection()

    assert attempted is False


def test_remote_exasol_with_tls_verification_reaches_connect(monkeypatch):
    captured = {}
    connection = object()

    monkeypatch.setenv("EXASOL_DSN", "db.example.com:8563")
    monkeypatch.setenv("EXASOL_PASSWORD", "remote-test-password")
    monkeypatch.setenv("EXASOL_TLS_VERIFY", "true")
    monkeypatch.setattr(
        db.pyexasol,
        "connect",
        lambda **kwargs: captured.update(kwargs) or connection,
    )

    assert db.get_connection() is connection
    assert captured["dsn"] == "db.example.com:8563"
    assert captured["websocket_sslopt"]["cert_reqs"] == ssl.CERT_REQUIRED


def test_remote_configuration_error_does_not_reveal_credentials(monkeypatch):
    dsn = "dsn-user:dsn-secret@db.example.com:8563"
    password = "password-secret"
    monkeypatch.setenv("EXASOL_DSN", dsn)
    monkeypatch.setenv("EXASOL_PASSWORD", password)
    monkeypatch.setenv("EXASOL_TLS_VERIFY", "false")

    with pytest.raises(ValueError) as error:
        db.get_connection()

    message = str(error.value)
    assert dsn not in message
    assert "dsn-secret" not in message
    assert password not in message


@pytest.mark.parametrize("dsn", [
    "127.0.0.1:8563",
    "localhost:8563",
    "localhost.:8563",
    "[::1]:8563",
    "[::ffff:127.0.0.1]:8563",
])
def test_loopback_dsn_detection_accepts_local_hosts(dsn):
    assert db._is_loopback_dsn(dsn) is True


@pytest.mark.parametrize("dsn", [
    "db.example.com:8563",
    "127.0.0.1.attacker.example:8563",
    "localhost.example:8563",
    "10.0.0.4:8563",
])
def test_loopback_dsn_detection_rejects_remote_hosts(dsn):
    assert db._is_loopback_dsn(dsn) is False


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


def test_incident_list_and_trend_use_the_shared_incident_flag(monkeypatch):
    class Result:
        def fetchall(self):
            return []

    class Connection:
        def __init__(self):
            self.queries = []

        def execute(self, query):
            self.queries.append(query)
            return Result()

        def close(self):
            pass

    incident_connection = Connection()
    trend_connection = Connection()
    connections = iter([incident_connection, trend_connection])
    monkeypatch.setattr(db, "get_connection", lambda: next(connections))

    db.get_failed_pipelines()
    db.get_pipeline_trend()

    incident_query = incident_connection.queries[0]
    trend_query = trend_connection.queries[0]
    assert "FROM OPSINTEL.PIPELINE_HEALTH_FEATURES" in incident_query
    assert "WHERE IS_INCIDENT = 1" in incident_query
    assert "SUM( IS_INCIDENT ) AS INCIDENT_COUNT" in " ".join(
        trend_query.split()
    )


def test_health_feature_incident_and_completeness_semantics():
    connection = duckdb.connect(":memory:")
    connection.execute("CREATE SCHEMA OPSINTEL")
    connection.execute("""
        CREATE TABLE OPSINTEL.PIPELINE_RUNS (
            RUN_ID INTEGER,
            PIPELINE_NAME VARCHAR,
            RUN_STATUS VARCHAR,
            EXPECTED_ROWS INTEGER,
            ACTUAL_ROWS INTEGER,
            RUN_TIME TIMESTAMP
        )
    """)
    connection.execute("""
        INSERT INTO OPSINTEL.PIPELINE_RUNS VALUES
        (1, 'equal', 'SUCCESS', 10, 10, '2026-10-19 01:00:00'),
        (2, 'lower', 'SUCCESS', 10, 8, '2026-10-19 01:01:00'),
        (3, 'higher', 'SUCCESS', 10, 12, '2026-10-19 01:02:00'),
        (4, 'expected-null', 'SUCCESS', NULL, 10, '2026-10-19 01:03:00'),
        (5, 'actual-null', 'SUCCESS', 10, NULL, '2026-10-19 01:04:00'),
        (6, 'both-null', 'SUCCESS', NULL, NULL, '2026-10-19 01:05:00'),
        (7, 'failed-match', 'FAILED', 10, 10, '2026-10-19 01:06:00'),
        (8, 'both-zero', 'SUCCESS', 0, 0, '2026-10-19 01:07:00'),
        (9, 'zero-excess', 'SUCCESS', 0, 5, '2026-10-19 01:08:00'),
        (10, 'failed-null', 'FAILED', NULL, NULL, '2026-10-19 01:09:00')
    """)
    view_sql = Path("sql/analysis/pipeline_health_features.sql").read_text()
    connection.execute(view_sql)

    rows = connection.execute("""
        SELECT PIPELINE_NAME, IS_INCIDENT, MISSING_ROWS, EXCESS_ROWS,
               COMPLETENESS_PCT
        FROM OPSINTEL.PIPELINE_HEALTH_FEATURES
        ORDER BY RUN_ID
    """).fetchall()

    assert rows == [
        ("equal", 0, 0, 0, 100.0),
        ("lower", 1, 2, 0, 80.0),
        ("higher", 1, 0, 2, 120.0),
        ("expected-null", 0, None, None, None),
        ("actual-null", 0, None, None, None),
        ("both-null", 0, None, None, None),
        ("failed-match", 1, 0, 0, 100.0),
        ("both-zero", 0, 0, 0, 100.0),
        ("zero-excess", 1, 0, 5, None),
        ("failed-null", 1, None, None, None),
    ]
