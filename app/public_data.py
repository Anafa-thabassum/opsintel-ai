"""Public GitHub issue ingestion and Exasol-backed investigation.

Only short, screened excerpts are stored. Original issue bodies remain at GitHub.
"""

import csv
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from app.classification import classify_incident
from app.db import get_connection
from app.fingerprint import FINGERPRINT_VERSION, compare_fingerprints, normalize_log, token_ngrams


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evaluation" / "public_source_registry_v1.json"
PROJECT_LABELS = ROOT / "evaluation" / "public_failure_corpus_v2.csv"
_DIAGNOSTIC = re.compile(r"\b(?:error|fail(?:ed|ure|s)?|timeout|timed out|exception|invalid|undefined|not found|mismatch)\b|\b[A-Za-z_]+(?:Error|Exception|Timeout)\b", re.I)
_SENSITIVE = re.compile(r"(?i)\b(?:password|secret|access[_ -]?token|authorization|api[_ -]?key)\b|@|(?:https?://[^\s]*[?&])")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_ABS_PATH = re.compile(r"(?<!\w)/(?:[\w.-]+/){2,}[\w.-]+")
_CREDENTIAL = re.compile(r"(?i)\b(?:password|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*\S+|\bBearer\s+\S+|\b(?:ghp_|github_pat_)[A-Za-z0-9_]+")
_COLUMNS = "SOURCE_KEY, SOURCE_NAME, SOURCE_REPOSITORY, ISSUE_NUMBER, SOURCE_URL, TITLE, EXCERPT, EXCERPT_ORIGIN, SOURCE_STATE, SOURCE_CREATED_AT, SOURCE_UPDATED_AT, COLLECTED_AT, BODY_SHA256, PROJECT_LABEL, LABEL_STATUS, CLASSIFIER_CATEGORY, CLASSIFICATION_JSON, CODE_LICENSE, CODE_LICENSE_URL, ISSUE_TEXT_LICENSE_STATUS"


def _utc_sql(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Source timestamp must include a timezone")
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _screen(text):
    text = " ".join(str(text or "").split())[:1000]
    text = _CREDENTIAL.sub("[credential redacted]", text)
    text = _EMAIL.sub("[email redacted]", text)
    text = _IP.sub("[IP redacted]", text)
    text = _ABS_PATH.sub("[path redacted]", text)
    return text


def _excerpt(issue):
    candidates = []
    for number, raw in enumerate((issue.get("body") or "").splitlines(), start=1):
        line = raw.strip().strip("`> ")
        hypothetical = re.search(r"\b(?:should|could|would|might|for example|something along the lines)\b", line, re.I)
        if 15 <= len(line) <= 350 and _DIAGNOSTIC.search(line) and not _SENSITIVE.search(line) and not hypothetical:
            screened = _screen(line)
            if len(screened) >= 15:
                score = 3 if re.search(r"\b[A-Za-z_]+(?:Error|Exception|Timeout)\b|SQLSTATE\s*\d+", line) else 0
                score += 3 if re.search(r"\b(?:timed out|no module named|undefined|invalid identifier|schema mismatch)\b", line, re.I) else 0
                score += 1 if re.search(r"\btimeout\b", line, re.I) else 0
                score += 1 if len(line) <= 180 else 0
                candidates.append((score, -len(line), -number, screened, f"body-line-{number}"))
    if candidates:
        _, _, _, excerpt, origin = max(candidates)
        return excerpt, origin
    return _screen(issue["title"]), "title"


def source_registry():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if registry.get("version") != "github-issues-v1":
        raise ValueError("Unsupported public source registry")
    return registry


def _project_labels():
    with PROJECT_LABELS.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        labels = {}
        for row in rows:
            parts = urlsplit(row["source_url"]).path.strip("/").split("/")
            if len(parts) != 4 or parts[2] != "issues":
                continue
            repository = f"{parts[0]}/{parts[1]}".replace("dbt-labs/dbt-core", "dbt-labs/dbt")
            labels[f"{repository}#{parts[3]}"] = row["expected"]
        return labels


def fetch_issue(repository, number, *, opener=urlopen, retries=2, delay=time.sleep):
    """Fetch one issue via the official API, with bounded retries."""
    url = f"https://api.github.com/repos/{repository}/issues/{int(number)}"
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": "opsintel-public-incident-ingest/1"}
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(retries + 1):
        try:
            with opener(Request(url, headers=headers), timeout=15) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code == 403 and exc.headers.get("X-RateLimit-Remaining") == "0":
                reset = exc.headers.get("X-RateLimit-Reset")
                try:
                    retry_at = datetime.fromtimestamp(int(reset), tz=timezone.utc).isoformat()
                except (TypeError, ValueError, OverflowError):
                    retry_at = "the GitHub rate-limit reset"
                raise RuntimeError(f"GitHub API rate limit exhausted for {repository}#{number}; "
                                   f"retry after {retry_at} or set GITHUB_TOKEN") from exc
            retryable = exc.code in {429, 500, 502, 503, 504} or (exc.code == 403 and exc.headers.get("X-RateLimit-Remaining") != "0")
            if not retryable or attempt == retries:
                raise RuntimeError(f"GitHub issue API returned HTTP {exc.code} for {repository}#{number}") from exc
            delay(min(2 ** attempt, 4))
        except URLError as exc:
            if attempt == retries:
                raise RuntimeError(f"GitHub issue API was unavailable for {repository}#{number}") from exc
            delay(min(2 ** attempt, 4))
    raise RuntimeError("Unreachable retry state")


def normalize_issue(issue, source, *, collected_at=None, project_label=None):
    repository = source["repository"]
    number = int(issue["number"])
    url = f"https://github.com/{repository}/issues/{number}"
    if issue.get("html_url") != url or "pull_request" in issue:
        raise ValueError(f"Unexpected source identity for {repository}#{number}")
    title = _screen(issue.get("title"))
    if not title:
        raise ValueError("Public issue is missing a title")
    excerpt, origin = _excerpt(issue)
    collected = _utc_sql(collected_at or datetime.now(timezone.utc).isoformat())
    evidence_ref = f"github:{repository}#{number}:{origin}"
    assessment = classify_incident([{"reference": evidence_ref, "source": url, "observation": excerpt}])
    classification = assessment["classification"]
    return {
        "source_key": f"{repository}#{number}", "source_name": source["name"],
        "source_repository": repository, "issue_number": number, "source_url": url,
        "title": title, "excerpt": excerpt, "excerpt_origin": origin,
        "source_state": issue.get("state") if issue.get("state") in {"open", "closed"} else "unknown",
        "source_created_at": _utc_sql(issue["created_at"]),
        "source_updated_at": _utc_sql(issue["updated_at"]),
        "collected_at": collected,
        "body_sha256": hashlib.sha256((issue.get("body") or "").encode("utf-8")).hexdigest(),
        "project_label": project_label,
        "label_status": "project_assigned_unreviewed" if project_label else "unlabelled",
        "classifier_category": assessment["result"][0],
        "classification": classification,
        "code_license": source["code_license"], "code_license_url": source["code_license_url"],
        "issue_text_license_status": source["issue_text_license_status"],
    }


def _record(row):
    keys = ("source_key", "source_name", "source_repository", "issue_number", "source_url", "title",
            "excerpt", "excerpt_origin", "source_state", "source_created_at", "source_updated_at",
            "collected_at", "body_sha256", "project_label", "label_status", "classifier_category",
            "classification", "code_license", "code_license_url", "issue_text_license_status")
    item = dict(zip(keys, row))
    item["issue_number"] = int(item["issue_number"])
    item["classification"] = json.loads(item["classification"])
    for name in ("source_created_at", "source_updated_at", "collected_at"):
        item[name] = str(item[name])
    return item


def ingest_issue(connection, record):
    current = connection.execute("""
        SELECT BODY_SHA256, SOURCE_UPDATED_AT, EXCERPT, EXCERPT_ORIGIN, CLASSIFIER_CATEGORY
        FROM OPSINTEL.PUBLIC_INCIDENTS
        WHERE SOURCE_KEY = {source_key}
    """, {"source_key": record["source_key"]}).fetchone()
    if (current and str(current[0]) == record["body_sha256"]
            and datetime.fromisoformat(str(current[1])) == datetime.fromisoformat(record["source_updated_at"])
            and str(current[2]) == record["excerpt"] and str(current[3]) == record["excerpt_origin"]
            and str(current[4]) == record["classifier_category"]):
        return "unchanged"
    values = {**record, "classification": json.dumps(record["classification"], sort_keys=True)}
    if current:
        connection.execute("""
            UPDATE OPSINTEL.PUBLIC_INCIDENTS SET
                SOURCE_NAME={source_name}, SOURCE_REPOSITORY={source_repository}, ISSUE_NUMBER={issue_number!d},
                SOURCE_URL={source_url}, TITLE={title}, EXCERPT={excerpt}, EXCERPT_ORIGIN={excerpt_origin},
                SOURCE_STATE={source_state}, SOURCE_CREATED_AT={source_created_at}, SOURCE_UPDATED_AT={source_updated_at},
                COLLECTED_AT={collected_at}, BODY_SHA256={body_sha256}, PROJECT_LABEL={project_label},
                LABEL_STATUS={label_status}, CLASSIFIER_CATEGORY={classifier_category},
                CLASSIFICATION_JSON={classification}, CODE_LICENSE={code_license}, CODE_LICENSE_URL={code_license_url},
                ISSUE_TEXT_LICENSE_STATUS={issue_text_license_status}
            WHERE SOURCE_KEY={source_key}
        """, values)
        return "updated"
    connection.execute("""
        INSERT INTO OPSINTEL.PUBLIC_INCIDENTS
        (SOURCE_KEY, SOURCE_NAME, SOURCE_REPOSITORY, ISSUE_NUMBER, SOURCE_URL, TITLE, EXCERPT,
         EXCERPT_ORIGIN, SOURCE_STATE, SOURCE_CREATED_AT, SOURCE_UPDATED_AT, COLLECTED_AT,
         BODY_SHA256, PROJECT_LABEL, LABEL_STATUS, CLASSIFIER_CATEGORY, CLASSIFICATION_JSON,
         CODE_LICENSE, CODE_LICENSE_URL, ISSUE_TEXT_LICENSE_STATUS)
        VALUES ({source_key}, {source_name}, {source_repository}, {issue_number!d}, {source_url},
                {title}, {excerpt}, {excerpt_origin}, {source_state}, {source_created_at},
                {source_updated_at}, {collected_at}, {body_sha256}, {project_label},
                {label_status}, {classifier_category}, {classification}, {code_license},
                {code_license_url}, {issue_text_license_status})
    """, values)
    return "inserted"


def ingest_registered(*, repository=None, fetch=fetch_issue):
    registry = source_registry()
    labels = _project_labels()
    results = []
    connection = get_connection()
    try:
        for source in registry["sources"]:
            if repository and source["repository"] != repository:
                continue
            for number in source["issue_numbers"]:
                try:
                    issue = fetch(source["api_repository"], number)
                    record = normalize_issue(issue, source, project_label=labels.get(f"{source['repository']}#{number}"))
                    action = ingest_issue(connection, record)
                    results.append({"source_key": record["source_key"], "action": action})
                except (KeyError, ValueError, RuntimeError) as exc:
                    results.append({"source_key": f"{source['repository']}#{number}",
                                    "action": "failed", "error": str(exc)})
        return results
    finally:
        connection.close()


def remove_public_issue(source_key):
    """Physically remove locally cached public text, including its metadata row."""
    connection = get_connection()
    try:
        connection.execute("DELETE FROM OPSINTEL.PUBLIC_INCIDENTS WHERE SOURCE_KEY = {source_key}",
                           {"source_key": source_key})
    finally:
        connection.close()


def list_public_incidents(*, source=None, category=None, search=None, limit=50, offset=0):
    conditions = []
    params = {"limit": min(max(int(limit), 1), 200), "offset": max(int(offset), 0)}
    if source:
        conditions.append("SOURCE_REPOSITORY = {source}")
        params["source"] = source
    if category:
        conditions.append("CLASSIFIER_CATEGORY = {category}")
        params["category"] = category
    if search:
        conditions.append("(LOWER(TITLE) LIKE {search} OR LOWER(EXCERPT) LIKE {search})")
        params["search"] = f"%{search.lower()[:120]}%"
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    connection = get_connection()
    try:
        total = int(connection.execute(f"SELECT COUNT(*) FROM OPSINTEL.PUBLIC_INCIDENTS {where}", params).fetchone()[0])
        rows = connection.execute(f"""
            SELECT {_COLUMNS} FROM OPSINTEL.PUBLIC_INCIDENTS {where}
            ORDER BY SOURCE_CREATED_AT DESC, SOURCE_KEY
            LIMIT {{limit!d}} OFFSET {{offset!d}}
        """, params).fetchall()
        return {"total": total, "incidents": [_record(row) for row in rows]}
    finally:
        connection.close()


def get_public_incident(source_key):
    connection = get_connection()
    try:
        row = connection.execute(f"SELECT {_COLUMNS} FROM OPSINTEL.PUBLIC_INCIDENTS WHERE SOURCE_KEY = {{source_key}}",
                                 {"source_key": source_key}).fetchone()
        return _record(row) if row else None
    finally:
        connection.close()


def public_analytics():
    connection = get_connection()
    try:
        rows = connection.execute("""
            SELECT SOURCE_NAME, CLASSIFIER_CATEGORY, LABEL_STATUS, COUNT(*)
            FROM OPSINTEL.PUBLIC_INCIDENTS
            GROUP BY SOURCE_NAME, CLASSIFIER_CATEGORY, LABEL_STATUS
            ORDER BY SOURCE_NAME, CLASSIFIER_CATEGORY
        """).fetchall()
        total = sum(int(row[3]) for row in rows)
        return {"total": total, "unresolved": sum(int(row[3]) for row in rows if row[1] == "unclassified"),
                "groups": [{"source": row[0], "category": row[1], "label_status": row[2], "count": int(row[3])}
                           for row in rows]}
    finally:
        connection.close()


def evaluate_public_records():
    """Compare current symptoms with project labels; no causal accuracy claim."""
    records = []
    offset = 0
    while True:
        page = list_public_incidents(limit=200, offset=offset)
        records.extend(page["incidents"])
        offset += len(page["incidents"])
        if offset >= page["total"] or not page["incidents"]:
            break
    labelled = [item for item in records if item["project_label"]]
    results = []
    for item in records:
        ref = f"github:{item['source_key']}:{item['excerpt_origin']}"
        assessment = classify_incident([{"reference": ref, "source": item["source_url"],
                                         "observation": item["excerpt"]}])
        classification = assessment["classification"]
        provenance_valid = (item["source_url"] ==
                            f"https://github.com/{item['source_repository']}/issues/{item['issue_number']}"
                            and item["source_key"] == f"{item['source_repository']}#{item['issue_number']}"
                            and bool(item["excerpt"] and item["excerpt_origin"] and item["body_sha256"]))
        results.append({"source_key": item["source_key"], "expected": item["project_label"],
                        "predicted": assessment["result"][0],
                        "correct": assessment["result"][0] == item["project_label"] if item["project_label"] else None,
                        "status": classification["status"],
                        "traceable": bool(provenance_valid and all(
                            ref in signal["evidence_refs"] for signal in classification["signals"])),
                        "source_url": item["source_url"]})
    scored = [item for item in results if item["expected"]]
    correct = sum(item["correct"] for item in scored)
    return {"total_collected": len(records), "project_labelled": len(labelled),
            "unlabelled": len(records) - len(labelled),
            "exact_category_matches": correct,
            "exact_category_accuracy": round(correct / len(scored), 4) if scored else None,
            "unresolved_rate": round(sum(item["status"] == "unresolved" for item in results) / len(results), 4) if results else None,
            "evidence_coverage": round(sum(item["traceable"] for item in results) / len(results), 4) if results else None,
            "false_match_rate": None,
            "label_provenance": "project-assigned mapping from the historical public scorecard; no independent adjudication",
            "limitations": "Issue excerpts are short and may omit material context. No verified causes exist in this corpus.",
            "results": results}


def similar_public_incidents(source_key):
    """Compare public excerpts as text only; these are never causal matches."""
    current = get_public_incident(source_key)
    if current is None:
        return None
    pages = []
    offset = 0
    while True:
        page = list_public_incidents(limit=200, offset=offset)
        pages.extend(page["incidents"])
        offset += len(page["incidents"])
        if offset >= page["total"] or not page["incidents"]:
            break

    def fingerprint(item):
        tokens = token_ngrams(normalize_log(item["excerpt"]))
        category = item["classifier_category"]
        return {"version": FINGERPRINT_VERSION, "tokens": sorted(tokens),
                "features": {"symptom_category": category} if category != "unclassified" else {}}

    baseline = fingerprint(current)
    matches = []
    for item in pages:
        if item["source_key"] == source_key:
            continue
        comparison = compare_fingerprints(baseline, fingerprint(item))
        if comparison["eligible"] and comparison.get("matching_tokens") and comparison["score"] >= 0.2:
            matches.append({"source_key": item["source_key"], "title": item["title"],
                            "source_url": item["source_url"], "similarity_score": comparison["score"],
                            "matching_tokens": comparison["matching_tokens"],
                            "matching_features": comparison["matching_features"],
                            "differing_features": comparison["differing_features"],
                            "status": "unverified_public_text_similarity"})
    matches.sort(key=lambda item: (-item["similarity_score"], item["source_key"]))
    return {"source_key": source_key, "matches": matches[:3],
            "notice": "Text similarity is a retrieval score, not a verified cause or diagnosis probability."}
