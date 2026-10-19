"""Create or reset the synthetic OpsIntel demonstration database."""

import argparse
from pathlib import Path

from app.db import get_connection


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = ROOT / "sql/schema.sql"
SEED_FILE = ROOT / "sql/seed.sql"
ANALYTICS_FILE = ROOT / "sql/analysis/pipeline_health_features.sql"
CASCADE_FILE = ROOT / "sql/analysis/pipeline_dependency_cascade.sql"


def load_statements(path):
    sql = "\n".join(
        line for line in path.read_text().splitlines()
        if not line.lstrip().startswith("--")
    )
    statements = []
    current = []
    in_string = False
    index = 0

    while index < len(sql):
        character = sql[index]
        current.append(character)

        if character == "'":
            if in_string and index + 1 < len(sql) and sql[index + 1] == "'":
                current.append(sql[index + 1])
                index += 1
            else:
                in_string = not in_string
        elif character == ";" and not in_string:
            statement = "".join(current[:-1]).strip()
            if statement:
                statements.append(statement)
            current = []

        index += 1

    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset",
        action="store_true",
        help="drop and recreate the synthetic OPSINTEL schema",
    )
    args = parser.parse_args()

    connection = get_connection()

    try:
        schema_exists = int(connection.execute("""
            SELECT COUNT(*)
            FROM EXA_ALL_SCHEMAS
            WHERE SCHEMA_NAME = 'OPSINTEL'
        """).fetchone()[0]) > 0

        if args.reset and schema_exists:
            connection.execute("DROP SCHEMA OPSINTEL CASCADE")
            schema_exists = False

        if not schema_exists:
            for path in (SCHEMA_FILE, SEED_FILE):
                for statement in load_statements(path):
                    connection.execute(statement)

        for path in (ANALYTICS_FILE, CASCADE_FILE):
            for statement in load_statements(path):
                connection.execute(statement)
    finally:
        connection.close()

    action = "reset" if args.reset else "prepared"
    print(f"OPSINTEL demo database {action} successfully.")


if __name__ == "__main__":
    main()
