"""Exasol-backed verified incident memory. Retrieval never confirms a cause."""

import json
from datetime import datetime, timezone
from uuid import uuid4

from app.db import get_connection
from app.classification import classify_incident
from app.fingerprint import FINGERPRINT_VERSION, compare_fingerprints, fingerprint_incident


SUPPORTED_CATEGORIES = frozenset({
    "delayed_run", "duplicate_data", "timeout", "schema_mismatch",
    "dependency_failure", "early_termination", "incomplete_data",
})
CHECKLIST_VERSION = "cause-verification-v1"
# These are mandatory reviewer attestations, not empirical proof of causation.
CLASS_CRITERIA = {
    "delayed_run": ("scheduler_timing", "delay_mechanism", "causal_link"),
    "duplicate_data": ("duplicate_keys", "replay_or_source_lineage", "causal_link"),
    "timeout": ("configured_limit", "limiting_mechanism", "causal_link"),
    "schema_mismatch": ("field_type_mismatch", "versioned_schema_change", "causal_link"),
    "dependency_failure": ("required_dependency", "upstream_failure", "downstream_link"),
    "early_termination": ("premature_end", "termination_event", "causal_link"),
    "incomplete_data": ("same_scope_shortfall", "missing_row_reconciliation", "causal_link"),
}
COMMON_CRITERIA = ("alternatives_reviewed", "contradictions_resolved")
MIN_SIMILARITY = 0.42


class MemoryConflict(ValueError):
    """The requested memory transition conflicts with current state."""


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _decode(value, default=None):
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _transaction(operation):
    connection = get_connection()
    try:
        connection.set_autocommit(False)
        result = operation(connection)
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _read(operation):
    connection = get_connection()
    try:
        return operation(connection)
    finally:
        connection.close()


def _incident_from_row(row):
    if not row:
        return None
    fingerprint = _decode(row[6])
    evidence = _decode(row[7])
    if not isinstance(fingerprint, dict) or not isinstance(evidence, list):
        return None
    return {
        "incident_id": str(row[0]), "run_id": int(row[1]),
        "pipeline_name": str(row[2]), "confirmed_category": str(row[3]),
        "confirmed_description": str(row[4]), "fingerprint_version": str(row[5]),
        "fingerprint": fingerprint, "evidence": evidence,
        "confirmed_by": str(row[8]), "confirmed_at": str(row[9]),
        "status": str(row[10]), "source_incident_id": row[11],
        "revision": int(row[12]),
    }


_INCIDENT_COLUMNS = """INCIDENT_ID, RUN_ID, PIPELINE_NAME, CONFIRMED_CATEGORY,
    CONFIRMED_DESCRIPTION, FINGERPRINT_VERSION, FINGERPRINT_JSON, EVIDENCE_JSON,
    CONFIRMED_BY, CONFIRMED_AT, STATUS, SOURCE_INCIDENT_ID, REVISION"""


def get_confirmed(run_id):
    def read(connection):
        row = connection.execute(f"""
            SELECT {_INCIDENT_COLUMNS} FROM OPSINTEL.CONFIRMED_INCIDENTS
            WHERE RUN_ID = {{run_id!d}}
        """, {"run_id": int(run_id)}).fetchone()
        return _incident_from_row(row)
    return _read(read)


def list_confirmed():
    def read(connection):
        rows = connection.execute(f"""
            SELECT {_INCIDENT_COLUMNS} FROM OPSINTEL.CONFIRMED_INCIDENTS
            ORDER BY CONFIRMED_AT DESC
        """).fetchall()
        return [item for row in rows if (item := _incident_from_row(row))]
    return _read(read)


def memory_analytics():
    """Operational counts computed in Exasol; these are not accuracy metrics."""
    def read(connection):
        categories = connection.execute("""
            SELECT CONFIRMED_CATEGORY, COUNT(*) FROM OPSINTEL.CONFIRMED_INCIDENTS
            WHERE STATUS = 'active' GROUP BY CONFIRMED_CATEGORY
            ORDER BY CONFIRMED_CATEGORY
        """).fetchall()
        statuses = connection.execute("""
            SELECT STATUS, COUNT(*) FROM OPSINTEL.CONFIRMED_INCIDENTS
            GROUP BY STATUS ORDER BY STATUS
        """).fetchall()
        decisions = connection.execute("""
            SELECT MATCH_STATUS, COUNT(*) FROM OPSINTEL.INCIDENT_MATCHES
            GROUP BY MATCH_STATUS ORDER BY MATCH_STATUS
        """).fetchall()
        return {"active_by_category": {str(row[0]): int(row[1]) for row in categories},
                "memory_status_counts": {str(row[0]): int(row[1]) for row in statuses},
                "match_status_counts": {str(row[0]): int(row[1]) for row in decisions},
                "notice": "These are Exasol operational counts, not measured classifier accuracy or false-match rates."}
    return _read(read)


def _submission_from_row(row):
    if not row:
        return None
    return {
        "submission_id": str(row[0]), "run_id": int(row[1]),
        "pipeline_name": str(row[2]), "kind": str(row[3]),
        "source_incident_id": row[4], "category": str(row[5]),
        "cause_description": str(row[6]), "evidence": _decode(row[7], []),
        "submitted_classification": _decode(row[8], {}),
        "fingerprint": _decode(row[9], {}), "submitted_by": str(row[10]),
        "submitted_at": str(row[11]), "status": str(row[12]),
        "reviewed_by": row[13], "reviewed_at": str(row[14]) if row[14] else None,
        "review_rationale": row[15], "checklist": _decode(row[16], None),
    }


_SUBMISSION_COLUMNS = """SUBMISSION_ID, RUN_ID, PIPELINE_NAME, KIND,
    SOURCE_INCIDENT_ID, CATEGORY, CAUSE_DESCRIPTION, EVIDENCE_JSON,
    CLASSIFICATION_JSON, FINGERPRINT_JSON, SUBMITTED_BY, SUBMITTED_AT, STATUS, REVIEWED_BY,
    REVIEWED_AT, REVIEW_RATIONALE, CHECKLIST_JSON"""


def get_submission(submission_id):
    def read(connection):
        row = connection.execute(f"""
            SELECT {_SUBMISSION_COLUMNS} FROM OPSINTEL.INCIDENT_SUBMISSIONS
            WHERE SUBMISSION_ID = {{submission_id}}
        """, {"submission_id": submission_id}).fetchone()
        return _submission_from_row(row)
    return _read(read)


def list_submissions():
    def read(connection):
        rows = connection.execute(f"""
            SELECT {_SUBMISSION_COLUMNS} FROM OPSINTEL.INCIDENT_SUBMISSIONS
            ORDER BY SUBMITTED_AT DESC LIMIT 200
        """).fetchall()
        return [item for row in rows if (item := _submission_from_row(row))]
    return _read(read)


def submit_hypothesis(incident, *, category, description, evidence, actor_id, kind="new", source_incident_id=None):
    if category not in SUPPORTED_CATEGORIES:
        raise ValueError("Unsupported incident category")
    if kind not in {"new", "correction"}:
        raise ValueError("Unsupported submission kind")
    if not description or len(description.strip()) < 12:
        raise ValueError("A specific causal description is required")
    if not evidence:
        raise ValueError("Source-backed evidence is required")
    known_refs = {}
    for source in incident.get("evidence", []):
        if source.get("reference"):
            known_refs.setdefault(source["reference"], set()).add(str(source.get("observation", "")))
    for item in evidence:
        reference = item.get("reference")
        uri = item.get("source_uri")
        if item.get("kind") not in {"symptom", "causal"}:
            raise ValueError("Evidence kind must distinguish symptom from causal evidence")
        if not reference or (reference not in known_refs and not (uri and uri.startswith("https://") and reference == uri)):
            raise ValueError("Every evidence reference must resolve to incident evidence or an HTTPS source URI")
        if not item.get("excerpt"):
            raise ValueError("Every evidence reference needs an inspectable excerpt")
        if reference in known_refs and item["excerpt"] not in known_refs[reference]:
            raise ValueError("Incident evidence excerpt must match the referenced source record")
    current = get_confirmed(incident["run_id"])
    if kind == "new" and current is not None:
        raise MemoryConflict("This run already has a confirmation; submit a correction")
    if kind == "correction" and (current is None or current["status"] not in {"active", "revoked"} or current["incident_id"] != source_incident_id):
        raise MemoryConflict("Correction must reference the current confirmed incident record")
    submission_id = str(uuid4())
    packet = [dict(item) for item in evidence]
    symptom_refs = {item["reference"] for item in packet if item["kind"] == "symptom"}
    causal_refs = {item["reference"] for item in packet if item["kind"] == "causal"}
    if not symptom_refs or not causal_refs or symptom_refs & causal_refs:
        raise ValueError("Submission requires distinct symptom and causal source references")
    symptom_evidence = [source for source in incident.get("evidence", [])
                        if source.get("reference") in symptom_refs and source.get("observation") in
                        {item["excerpt"] for item in packet if item["reference"] == source.get("reference")}]
    symptom_evidence.extend({"reference": item["reference"], "source": item["source_uri"],
                             "observation": item["excerpt"]}
                            for item in packet if item.get("source_uri") and item["kind"] == "symptom")
    symptom_classification = classify_incident(symptom_evidence, {"run_id": incident["run_id"]})["classification"]
    symptom_supported = {symptom_classification.get("symptom_category"),
                         *(symptom_classification.get("secondary_categories") or [])}
    if symptom_classification.get("status") != "supported" or category not in symptom_supported:
        raise ValueError("Symptom source evidence does not independently support the submitted category")
    added_evidence = [{"reference": item["reference"], "source": item["source_uri"],
                       "observation": item["excerpt"]}
                      for item in packet if item.get("source_uri")]
    classification = classify_incident([*incident.get("evidence", []), *added_evidence],
                                       {"run_id": incident["run_id"]})["classification"]
    fingerprint = fingerprint_incident(incident)
    timestamp = _now()

    def write(connection):
        connection.execute("""
            INSERT INTO OPSINTEL.INCIDENT_SUBMISSIONS
            (SUBMISSION_ID, RUN_ID, PIPELINE_NAME, KIND, SOURCE_INCIDENT_ID,
             CATEGORY, CAUSE_DESCRIPTION, EVIDENCE_JSON, CLASSIFICATION_JSON, FINGERPRINT_JSON,
             SUBMITTED_BY, SUBMITTED_AT, STATUS)
            VALUES ({submission_id}, {run_id!d}, {pipeline_name}, {kind},
                    {source_incident_id}, {category}, {description}, {evidence},
                    {classification}, {fingerprint}, {actor_id}, {timestamp}, 'pending')
        """, {"submission_id": submission_id, "run_id": incident["run_id"],
              "pipeline_name": incident["pipeline_name"], "kind": kind,
              "source_incident_id": source_incident_id, "category": category,
              "description": description.strip(), "evidence": _json(packet),
              "classification": _json(classification),
              "fingerprint": _json(fingerprint), "actor_id": actor_id,
              "timestamp": timestamp})
    _transaction(write)
    return {"submission_id": submission_id, "status": "pending", "kind": kind, "checklist_version": CHECKLIST_VERSION}


def _validate_checklist(submission, checklist):
    if checklist.get("version") != CHECKLIST_VERSION:
        raise ValueError("Verification checklist version mismatch")
    required = set(CLASS_CRITERIA[submission["category"]]) | set(COMMON_CRITERIA)
    items = checklist.get("criteria")
    if not isinstance(items, list) or {item.get("id") for item in items} != required or len(items) != len(required):
        raise ValueError("Every required cause-specific and common criterion must be assessed exactly once")
    available_refs = {item.get("reference") for item in submission["evidence"]}
    causal_refs = {item.get("reference") for item in submission["evidence"] if item.get("kind") == "causal"}
    symptom_refs = {item.get("reference") for item in submission["evidence"] if item.get("kind") == "symptom"}
    symptom_criterion = CLASS_CRITERIA[submission["category"]][0]
    classification = submission.get("submitted_classification") or {}
    if classification.get("conflicts"):
        raise ValueError("Unresolved classifier conflicts block cause confirmation")
    supported = {classification.get("symptom_category"), *(classification.get("secondary_categories") or [])}
    if classification.get("status") != "supported" or submission["category"] not in supported:
        raise ValueError("Submitted evidence does not support the proposed symptom category")
    if not causal_refs or not symptom_refs or causal_refs & symptom_refs:
        raise ValueError("Cause confirmation requires distinct source-backed symptom and causal evidence")
    for item in items:
        if item.get("passed") is not True or not item.get("method") or not item.get("result"):
            raise ValueError("All mandatory criteria need a positive result and verification method")
        refs = item.get("evidence_refs")
        if not isinstance(refs, list) or not refs or any(ref not in available_refs for ref in refs):
            raise ValueError("Criterion evidence must reference the submitted source packet")
        if item["id"] == symptom_criterion and not symptom_refs.intersection(refs):
            raise ValueError("Symptom criterion requires a symptom evidence reference")
        if item["id"] in CLASS_CRITERIA[submission["category"]] and item["id"] != symptom_criterion and not causal_refs.intersection(refs):
            raise ValueError("Mechanism and causal-link checks require causal evidence references")
    if checklist.get("unresolved_conflicts"):
        raise ValueError("Material contradictions must be resolved before approval")


def _audit(connection, *, incident_id, submission_id, run_id, action, actor_id, rationale, before=None, after=None):
    connection.execute("""
        INSERT INTO OPSINTEL.INCIDENT_AUDIT
        (AUDIT_ID, INCIDENT_ID, SUBMISSION_ID, RUN_ID, AUDIT_ACTION, ACTOR_ID,
         RATIONALE, BEFORE_JSON, AFTER_JSON, CREATED_AT)
        VALUES ({audit_id}, {incident_id}, {submission_id}, {run_id!d},
                {action}, {actor_id}, {rationale}, {before}, {after}, {timestamp})
    """, {"audit_id": str(uuid4()), "incident_id": incident_id,
          "submission_id": submission_id, "run_id": run_id, "action": action,
          "actor_id": actor_id, "rationale": rationale, "before": _json(before) if before else None,
          "after": _json(after) if after else None, "timestamp": _now()})


def review_hypothesis(submission_id, *, decision, rationale, checklist, reviewer_id):
    submission = get_submission(submission_id)
    if submission is None:
        raise KeyError("Submission not found")
    if submission["status"] != "pending":
        raise MemoryConflict("Submission already reviewed")
    if submission["submitted_by"] == reviewer_id:
        raise MemoryConflict("Reviewer must differ from submitting investigator")
    if decision not in {"approve", "reject", "needs_more_evidence"}:
        raise ValueError("Invalid review decision")
    if not rationale or len(rationale.strip()) < 12:
        raise ValueError("A review rationale is required")
    if decision == "approve":
        _validate_checklist(submission, checklist)
    timestamp = _now()
    incident_id = submission["source_incident_id"] or str(uuid4())

    def write(connection):
        current_row = connection.execute(f"""
            SELECT {_INCIDENT_COLUMNS} FROM OPSINTEL.CONFIRMED_INCIDENTS
            WHERE RUN_ID = {{run_id!d}}
        """, {"run_id": submission["run_id"]}).fetchone()
        current = _incident_from_row(current_row)
        if decision == "approve":
            if submission["kind"] == "new" and current is not None:
                raise MemoryConflict("Run was confirmed while review was pending")
            if submission["kind"] == "correction" and (current is None or current["status"] not in {"active", "revoked"} or current["incident_id"] != incident_id):
                raise MemoryConflict("Original confirmation changed while review was pending")
            fingerprint = submission["fingerprint"]
            if submission["kind"] == "new":
                connection.execute("""
                    INSERT INTO OPSINTEL.CONFIRMED_INCIDENTS
                    (INCIDENT_ID, RUN_ID, PIPELINE_NAME, CONFIRMED_CATEGORY,
                     CONFIRMED_DESCRIPTION, FINGERPRINT_VERSION, FINGERPRINT_JSON,
                     EVIDENCE_JSON, CONFIRMED_BY, CONFIRMED_AT, STATUS,
                     SOURCE_INCIDENT_ID, REVISION)
                    VALUES ({incident_id}, {run_id!d}, {pipeline_name}, {category},
                            {description}, {version}, {fingerprint}, {evidence},
                            {reviewer_id}, {timestamp}, 'active', NULL, 1)
                """, {"incident_id": incident_id, "run_id": submission["run_id"],
                      "pipeline_name": submission["pipeline_name"], "category": submission["category"],
                      "description": submission["cause_description"], "version": FINGERPRINT_VERSION,
                      "fingerprint": _json(fingerprint), "evidence": _json(submission["evidence"]),
                      "reviewer_id": reviewer_id, "timestamp": timestamp})
            else:
                connection.execute("""
                    UPDATE OPSINTEL.INCIDENT_MATCHES SET MATCH_STATUS = 'stale'
                    WHERE MATCHED_INCIDENT_ID = {incident_id}
                      AND MATCH_STATUS IN ('candidate', 'rejected')
                """, {"incident_id": incident_id})
                connection.execute("""
                    UPDATE OPSINTEL.CONFIRMED_INCIDENTS
                    SET CONFIRMED_CATEGORY = {category}, CONFIRMED_DESCRIPTION = {description},
                        FINGERPRINT_VERSION = {version}, FINGERPRINT_JSON = {fingerprint},
                        EVIDENCE_JSON = {evidence}, CONFIRMED_BY = {reviewer_id},
                        CONFIRMED_AT = {timestamp}, STATUS = 'active', REVISION = {revision!d}
                    WHERE INCIDENT_ID = {incident_id}
                """, {"category": submission["category"], "description": submission["cause_description"],
                      "version": FINGERPRINT_VERSION, "fingerprint": _json(fingerprint),
                      "evidence": _json(submission["evidence"]), "reviewer_id": reviewer_id,
                      "timestamp": timestamp, "revision": current["revision"] + 1,
                      "incident_id": incident_id})
                connection.execute("""
                    DELETE FROM OPSINTEL.INCIDENT_FEATURES WHERE INCIDENT_ID = {incident_id}
                """, {"incident_id": incident_id})
            for name, value in fingerprint.get("features", {}).items():
                connection.execute("""
                    INSERT INTO OPSINTEL.INCIDENT_FEATURES
                    (INCIDENT_ID, FEATURE_NAME, FEATURE_VALUE, FEATURE_TYPE)
                    VALUES ({incident_id}, {name}, {value}, 'observed')
                """, {"incident_id": incident_id, "name": name, "value": str(value)})
            _audit(connection, incident_id=incident_id, submission_id=submission_id,
                   run_id=submission["run_id"], action="confirmed" if current is None else "corrected",
                   actor_id=reviewer_id, rationale=rationale, before=current,
                   after={"category": submission["category"], "description": submission["cause_description"],
                          "checklist": checklist, "evidence": submission["evidence"]})
        else:
            _audit(connection, incident_id=current["incident_id"] if current else None,
                   submission_id=submission_id, run_id=submission["run_id"], action=decision,
                   actor_id=reviewer_id, rationale=rationale, after={"checklist": checklist})
        connection.execute("""
            UPDATE OPSINTEL.INCIDENT_SUBMISSIONS
            SET STATUS = {status}, REVIEWED_BY = {reviewer_id}, REVIEWED_AT = {timestamp},
                REVIEW_RATIONALE = {rationale}, CHECKLIST_JSON = {checklist}
            WHERE SUBMISSION_ID = {submission_id}
        """, {"status": "approved" if decision == "approve" else decision,
              "reviewer_id": reviewer_id, "timestamp": timestamp, "rationale": rationale.strip(),
              "checklist": _json(checklist), "submission_id": submission_id})
    _transaction(write)
    return {"submission_id": submission_id, "decision": decision,
            "confirmed_root_cause": submission["cause_description"] if decision == "approve" else None,
            "incident_id": incident_id if decision == "approve" else None}


def revoke_confirmation(incident_id, *, rationale, reviewer_id):
    if not rationale or len(rationale.strip()) < 12:
        raise ValueError("Revocation rationale is required")

    def write(connection):
        row = connection.execute(f"""
            SELECT {_INCIDENT_COLUMNS} FROM OPSINTEL.CONFIRMED_INCIDENTS
            WHERE INCIDENT_ID = {{incident_id}}
        """, {"incident_id": incident_id}).fetchone()
        incident = _incident_from_row(row)
        if incident is None:
            raise KeyError("Confirmed incident not found")
        if incident["status"] != "active":
            raise MemoryConflict("Only active confirmations can be revoked")
        connection.execute("""
            UPDATE OPSINTEL.CONFIRMED_INCIDENTS SET STATUS = 'revoked'
            WHERE INCIDENT_ID = {incident_id}
        """, {"incident_id": incident_id})
        connection.execute("""
            UPDATE OPSINTEL.INCIDENT_MATCHES SET MATCH_STATUS = 'stale'
            WHERE MATCHED_INCIDENT_ID = {incident_id}
              AND MATCH_STATUS IN ('candidate', 'rejected')
        """, {"incident_id": incident_id})
        _audit(connection, incident_id=incident_id, submission_id=None,
               run_id=incident["run_id"], action="revoked", actor_id=reviewer_id,
               rationale=rationale, before=incident, after={"status": "revoked"})
        return {"incident_id": incident_id, "status": "revoked"}
    return _transaction(write)


def incident_history(run_id):
    def read(connection):
        rows = connection.execute("""
            SELECT AUDIT_ID, INCIDENT_ID, SUBMISSION_ID, AUDIT_ACTION, ACTOR_ID,
                   RATIONALE, BEFORE_JSON, AFTER_JSON, CREATED_AT
            FROM OPSINTEL.INCIDENT_AUDIT WHERE RUN_ID = {run_id!d}
            ORDER BY CREATED_AT, AUDIT_ID
        """, {"run_id": int(run_id)}).fetchall()
        return [{"audit_id": str(row[0]), "incident_id": row[1], "submission_id": row[2],
                 "action": str(row[3]), "actor_id": str(row[4]), "rationale": str(row[5]),
                 "before": _decode(row[6]), "after": _decode(row[7]), "created_at": str(row[8])}
                for row in rows]
    return _read(read)


def similar_incidents(incident, *, record=True):
    current = fingerprint_incident(incident)

    def read(connection):
        rows = connection.execute(f"""
            SELECT {_INCIDENT_COLUMNS} FROM OPSINTEL.CONFIRMED_INCIDENTS
            WHERE STATUS = 'active' AND RUN_ID <> {{run_id!d}}
            ORDER BY CONFIRMED_AT DESC LIMIT 500
        """, {"run_id": int(incident["run_id"])}).fetchall()
        prior = connection.execute("""
            SELECT MATCH_ID, MATCHED_INCIDENT_ID, MATCH_STATUS
            FROM OPSINTEL.INCIDENT_MATCHES WHERE SOURCE_RUN_ID = {run_id!d}
              AND MATCH_STATUS IN ('candidate', 'rejected')
            ORDER BY CREATED_AT, MATCH_ID
        """, {"run_id": int(incident["run_id"])}).fetchall()
        return ([item for row in rows if (item := _incident_from_row(row))],
                {str(row[1]): (str(row[0]), str(row[2])) for row in prior})
    candidates, prior = _read(read)
    matches = []
    for historical in candidates:
        existing = prior.get(historical["incident_id"])
        if existing and existing[1] == "rejected":
            continue
        comparison = compare_fingerprints(current, historical["fingerprint"])
        if not comparison["eligible"] or comparison["score"] < MIN_SIMILARITY:
            continue
        matches.append({
            "match_id": existing[0] if existing else str(uuid4()), "matched_incident_id": historical["incident_id"],
            "source_run_id": int(incident["run_id"]), "historical_run_id": historical["run_id"],
            "historical_confirmed_cause": historical["confirmed_description"],
            "historical_category": historical["confirmed_category"],
            "similarity_score": comparison["score"],
            "matching_features": comparison["matching_features"],
            "differing_features": comparison["differing_features"],
            "matching_tokens": comparison["matching_tokens"],
            "fingerprint_version": FINGERPRINT_VERSION,
            "confirmed_at": historical["confirmed_at"], "memory_status": historical["status"],
            "status": "candidate", "label": "Candidate based on verified historical incident — engineer verification required.",
        })
    matches.sort(key=lambda item: (-item["similarity_score"], item["matched_incident_id"]))
    matches = matches[:3]
    if record and matches:
        def write(connection):
            for match in matches:
                if match["matched_incident_id"] in prior:
                    continue
                connection.execute("""
                    INSERT INTO OPSINTEL.INCIDENT_MATCHES
                    (MATCH_ID, SOURCE_RUN_ID, MATCHED_INCIDENT_ID, SIMILARITY_SCORE,
                     FINGERPRINT_VERSION, MATCHING_FEATURES, DIFFERING_FEATURES,
                     MATCH_STATUS, CREATED_AT)
                    VALUES ({match_id}, {run_id!d}, {incident_id}, {score}, {version},
                            {matching}, {differing}, 'candidate', {timestamp})
                """, {"match_id": match["match_id"], "run_id": match["source_run_id"],
                      "incident_id": match["matched_incident_id"], "score": match["similarity_score"],
                      "version": FINGERPRINT_VERSION, "matching": _json(match["matching_features"]),
                      "differing": _json(match["differing_features"]), "timestamp": _now()})
        _transaction(write)
    return {"status": "candidates_available" if matches else "unresolved", "matches": matches,
            "reason": None if matches else "No sufficiently similar verified incident was found.",
            "score_notice": "Similarity is a retrieval score, not the probability that a diagnosis is correct."}


def reject_match(match_id, *, actor_id):
    def write(connection):
        row = connection.execute("""
            SELECT MATCH_STATUS FROM OPSINTEL.INCIDENT_MATCHES WHERE MATCH_ID = {match_id}
        """, {"match_id": match_id}).fetchone()
        if row is None:
            raise KeyError("Match not found")
        if str(row[0]) != "candidate":
            raise MemoryConflict("Match already reviewed")
        connection.execute("""
            UPDATE OPSINTEL.INCIDENT_MATCHES
            SET MATCH_STATUS = 'rejected', REVIEWED_BY = {actor_id}, REVIEWED_AT = {timestamp}
            WHERE MATCH_ID = {match_id}
        """, {"actor_id": actor_id, "timestamp": _now(), "match_id": match_id})
        return {"match_id": match_id, "status": "rejected"}
    return _transaction(write)
