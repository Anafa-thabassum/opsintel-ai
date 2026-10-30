"""Fetch registered public issues through GitHub's API into local Exasol."""

import argparse
import json

from app.public_data import ingest_registered, remove_public_issue


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", help="only ingest one registered repository")
    parser.add_argument("--remove", help="delete one cached source key, such as apache/airflow#46378")
    args = parser.parse_args()
    if args.remove:
        remove_public_issue(args.remove)
        print(json.dumps({"removed": args.remove}))
        return
    results = ingest_registered(repository=args.repository)
    print(json.dumps({"total": len(results), "results": results}, indent=2))
    if not results or any(item["action"] == "failed" for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
