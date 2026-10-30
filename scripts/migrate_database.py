"""Apply additive, versioned Exasol migrations without resetting demo data."""

import argparse
import hashlib
from pathlib import Path

from app.db import get_connection
from scripts.setup_database import load_statements


MIGRATIONS = Path(__file__).resolve().parents[1] / "sql" / "migrations"


def migrate(connection, *, apply=False):
    files = sorted(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql"))
    exists = int(connection.execute("""
        SELECT COUNT(*) FROM EXA_ALL_TABLES
        WHERE TABLE_SCHEMA = 'OPSINTEL' AND TABLE_NAME = 'SCHEMA_MIGRATIONS'
    """).fetchone()[0]) > 0
    if not exists:
        if not apply:
            return {"pending": [path.name for path in files], "applied": []}
        connection.execute("""
            CREATE TABLE OPSINTEL.SCHEMA_MIGRATIONS (
                VERSION VARCHAR(100) PRIMARY KEY,
                SHA256 VARCHAR(64) NOT NULL,
                APPLIED_AT TIMESTAMP NOT NULL
            )
        """)
    rows = connection.execute("SELECT VERSION, SHA256 FROM OPSINTEL.SCHEMA_MIGRATIONS").fetchall()
    applied = {str(row[0]): str(row[1]) for row in rows}
    pending = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if path.name in applied:
            if applied[path.name] != digest:
                raise ValueError(f"Applied migration changed: {path.name}")
            continue
        pending.append(path.name)
        if apply:
            for statement in load_statements(path):
                connection.execute(statement)
            connection.execute("""
                INSERT INTO OPSINTEL.SCHEMA_MIGRATIONS (VERSION, SHA256, APPLIED_AT)
                VALUES ({version}, {digest}, CURRENT_TIMESTAMP)
            """, {"version": path.name, "digest": digest})
    return {"pending": pending if not apply else [], "applied": sorted([*applied, *(pending if apply else [])])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="apply pending additive migrations")
    args = parser.parse_args()
    connection = get_connection()
    try:
        print(migrate(connection, apply=args.apply))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
