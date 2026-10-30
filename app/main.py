import os
import json
import secrets
import logging
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.db import (
    check_connection,
    get_failed_pipelines,
    get_failure_cascades,
    get_pipeline_trend,
)
from app.investigator import (
    assess_root_causes,
    attach_comparison_support,
    investigate_pipeline,
)
from app.llm import summarize_investigation
from app import memory, public_data
from scripts.evaluate_public_corpus import evaluate as evaluate_public_corpus

app = FastAPI(
    title="OpsIntel AI",
    description="Data incident detection and investigation platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_metrics(request, call_next):
    request_id = str(uuid4())
    started = time.perf_counter()
    response = await call_next(request)
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(latency_ms)
    logging.getLogger("opsintel.api").info(
        "request_id=%s method=%s path=%s status=%s latency_ms=%.1f",
        request_id, request.method, getattr(request.scope.get("route"), "path", "unmatched"),
        response.status_code, latency_ms,
    )
    return response


@app.get("/")
def home():
    return {
        "name": "OpsIntel AI",
        "status": "running",
    }


@app.get("/health")
def health():
    try:
        check_connection()
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        ) from exc


@app.get("/scorecard/public")
def public_scorecard():
    """Score only the repository's cited public failure-message corpus."""
    corpus = Path(__file__).resolve().parents[1] / "evaluation" / "public_failure_corpus_v2.csv"
    try:
        report = evaluate_public_corpus(corpus)
        return {
            **report,
            "dataset": "evaluation/public_failure_corpus_v2.csv",
            "data_notice": "Public source excerpts; expected categories are project mappings, not independently verified ground truth.",
            "transformations": "Each excerpt is classified by the current deterministic evidence classifier; exact category matches are counted.",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to evaluate the public data corpus",
        ) from exc


@app.get("/public/incidents")
def public_incidents(source: str | None = None, category: str | None = None,
                     search: str | None = None, limit: int = Query(default=50, ge=1, le=200),
                     offset: int = Query(default=0, ge=0)):
    try:
        return public_data.list_public_incidents(source=source, category=category,
                                                 search=search, limit=limit, offset=offset)
    except Exception as exc:
        raise HTTPException(503, "Public incident database is unavailable") from exc


@app.get("/public/sources")
def public_sources():
    try:
        registry = public_data.source_registry()
        return {"version": registry["version"], "sources": registry["sources"],
                "excluded_source": registry["excluded_source"]}
    except Exception as exc:
        raise HTTPException(503, "Public source registry is unavailable") from exc


@app.get("/public/analytics")
def public_incident_analytics():
    try:
        return public_data.public_analytics()
    except Exception as exc:
        raise HTTPException(503, "Public incident analytics are unavailable") from exc


@app.get("/public/evaluation")
def public_incident_evaluation():
    try:
        return public_data.evaluate_public_records()
    except Exception as exc:
        raise HTTPException(503, "Public incident evaluation is unavailable") from exc


@app.get("/public/incidents/{owner}/{repo}/{number}")
def public_incident(owner: str, repo: str, number: int):
    try:
        result = public_data.get_public_incident(f"{owner}/{repo}#{number}")
        if result is None:
            raise HTTPException(404, "Public incident not found")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, "Public incident database is unavailable") from exc


@app.get("/public/similar/{owner}/{repo}/{number}")
def public_similar(owner: str, repo: str, number: int):
    try:
        result = public_data.similar_public_incidents(f"{owner}/{repo}#{number}")
        if result is None:
            raise HTTPException(404, "Public incident not found")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, "Public similarity query is unavailable") from exc



@app.get("/analytics/trend")
def analytics_trend():
    try:
        rows = get_pipeline_trend()

        return {
            "trend": [
                {
                    "run_day": row[0],
                    "total_runs": int(row[1]),
                    "incident_count": int(row[2]),
                    "average_completeness_pct": (
                        float(row[3]) if row[3] is not None else None
                    ),
                    "average_rolling_failure_rate_pct": float(row[4]),
                    "daily_failure_rate_pct": (
                        float(row[5])
                        if len(row) > 5 and row[5] is not None
                        else None
                    ),
                }
                for row in rows
            ]
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve pipeline analytics",
        ) from exc




@app.get("/analytics/cascades")
def analytics_cascades():
    try:
        rows = get_failure_cascades()
        return {
            "count": len(rows),
            "cascades": [
                {
                    "root_pipeline": row[0],
                    "root_run_id": int(row[1]),
                    "root_run_time": row[2],
                    "downstream_pipeline": row[3],
                    "downstream_run_id": int(row[4]),
                    "downstream_run_time": row[5],
                    "dependency_depth": int(row[6]),
                    "dependency_path": row[7],
                    "correlation_lag_minutes": float(row[8]),
                }
                for row in rows
            ],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve failure cascades",
        ) from exc


@app.get("/incidents")
def list_incidents():
    try:
        rows = get_failed_pipelines()

        return {
            "count": len(rows),
            "incidents": [
                {
                    "run_id": row[0],
                    "pipeline_name": row[1],
                    "expected_rows": row[2],
                    "actual_rows": row[3],
                    "missing_rows": (
                        int(row[4]) if row[4] is not None else None
                    ),
                    "status": row[5],
                    "excess_rows": (
                        int(row[6]) if len(row) > 6 and row[6] is not None
                        else (
                            max(int(row[3]) - int(row[2]), 0)
                            if len(row) <= 6
                            and row[2] is not None
                            and row[3] is not None
                            else None
                        )
                    ),
                }
                for row in rows
            ],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve incidents",
        ) from exc


@app.get("/investigate/{run_id}")
def investigate(run_id: int):
    try:
        result = investigate_pipeline(run_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found",
            )

        root_causes = assess_root_causes(result)
        attach_comparison_support(result, root_causes)
        result["root_causes"] = root_causes
        result["causal_assessment"] = {
            "status": (
                "confirmed" if root_causes.get("confirmed_root_cause")
                else "candidates_available" if root_causes.get("candidates")
                else "not_assessed"
            ),
            "candidates": root_causes.get("candidates", []),
            "confirmed_root_cause": root_causes.get("confirmed_root_cause"),
        }
        result["llm_summary"] = summarize_investigation(result, root_causes)
        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Investigation failed",
        ) from exc


@app.get("/investigate/{run_id}/root-causes")
def root_cause_assessment(run_id: int):
    try:
        incident = investigate_pipeline(run_id)

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found",
            )

        return assess_root_causes(incident)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Root-cause assessment failed",
        ) from exc


def _memory_actor(authorization, *, reviewer=False):
    """Explicit token grants; absent configuration disables memory access."""
    try:
        grants = json.loads(os.getenv("OPSINTEL_AUTH_TOKENS_JSON", "{}"))
    except ValueError as exc:
        raise HTTPException(503, "Memory authorization is misconfigured") from exc
    if not isinstance(grants, dict) or not grants:
        raise HTTPException(503, "Memory authorization is not configured")
    token = authorization.removeprefix("Bearer ") if authorization and authorization.startswith("Bearer ") else ""
    actor = next((grant for secret, grant in grants.items()
                  if token and isinstance(secret, str) and secret and secrets.compare_digest(token, secret)), None)
    if not isinstance(actor, dict) or not isinstance(actor.get("actor_id"), str) or actor.get("role") not in {"investigator", "reviewer"}:
        raise HTTPException(401, "Valid engineer authorization required")
    if reviewer and actor["role"] != "reviewer":
        raise HTTPException(403, "Authorized root-cause reviewer required")
    return actor["actor_id"]


def _memory_error(exc):
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, KeyError):
        raise HTTPException(404, str(exc)) from exc
    if isinstance(exc, memory.MemoryConflict):
        raise HTTPException(409, str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(422, str(exc)) from exc
    raise HTTPException(503, "Verified memory database operation failed") from exc


class SourceEvidence(BaseModel):
    reference: str = Field(min_length=1, max_length=500)
    excerpt: str = Field(min_length=1, max_length=2000)
    kind: str = "symptom"
    source_uri: str | None = Field(default=None, max_length=1000)
    observed_at: str | None = Field(default=None, max_length=100)


class HypothesisSubmission(BaseModel):
    run_id: int
    category: str
    cause_description: str = Field(min_length=12, max_length=2000)
    evidence: list[SourceEvidence] = Field(min_length=1, max_length=20)
    kind: str = "new"
    source_incident_id: str | None = None


class CriterionResult(BaseModel):
    id: str
    passed: bool
    method: str
    result: str
    evidence_refs: list[str]


class VerificationChecklist(BaseModel):
    version: str
    criteria: list[CriterionResult]
    unresolved_conflicts: list[str] = []


class ReviewDecision(BaseModel):
    decision: str
    rationale: str = Field(min_length=12, max_length=2000)
    checklist: VerificationChecklist


class Rationale(BaseModel):
    rationale: str = Field(min_length=12, max_length=2000)


@app.get("/memory/criteria/{category}")
def memory_criteria(category: str, authorization: str | None = Header(default=None)):
    _memory_actor(authorization)
    if category not in memory.CLASS_CRITERIA:
        raise HTTPException(404, "Unsupported category")
    return {"version": memory.CHECKLIST_VERSION,
            "required": [*memory.CLASS_CRITERIA[category], *memory.COMMON_CRITERIA],
            "notice": "Reviewer attestations require source-backed causal evidence; symptom evidence alone cannot confirm a cause."}


@app.get("/memory/incidents")
def memory_incidents(authorization: str | None = Header(default=None)):
    _memory_actor(authorization)
    try:
        incidents = memory.list_confirmed()
        return {"count": len(incidents), "incidents": incidents}
    except Exception as exc:
        _memory_error(exc)


@app.get("/memory/analytics")
def memory_analytics(authorization: str | None = Header(default=None)):
    _memory_actor(authorization)
    try:
        return memory.memory_analytics()
    except Exception as exc:
        _memory_error(exc)


@app.get("/memory/incidents/{run_id}")
def memory_incident(run_id: int, authorization: str | None = Header(default=None)):
    _memory_actor(authorization)
    try:
        result = memory.get_confirmed(run_id)
        if result is None:
            raise HTTPException(404, "No confirmed incident for this run")
        return result
    except Exception as exc:
        _memory_error(exc)


@app.get("/memory/history/{run_id}")
def memory_history(run_id: int, authorization: str | None = Header(default=None)):
    _memory_actor(authorization)
    try:
        return {"run_id": run_id, "events": memory.incident_history(run_id)}
    except Exception as exc:
        _memory_error(exc)


@app.get("/memory/submissions")
def memory_submissions(authorization: str | None = Header(default=None)):
    _memory_actor(authorization)
    try:
        return {"submissions": memory.list_submissions()}
    except Exception as exc:
        _memory_error(exc)


@app.post("/memory/submissions", status_code=201)
def memory_submit(payload: HypothesisSubmission, authorization: str | None = Header(default=None)):
    actor_id = _memory_actor(authorization)
    try:
        incident = investigate_pipeline(payload.run_id)
        if incident is None:
            raise HTTPException(404, "Incident not found")
        return memory.submit_hypothesis(
            incident, category=payload.category,
            description=payload.cause_description,
            evidence=[item.model_dump() for item in payload.evidence],
            actor_id=actor_id, kind=payload.kind,
            source_incident_id=payload.source_incident_id,
        )
    except Exception as exc:
        _memory_error(exc)


@app.post("/memory/submissions/{submission_id}/review")
def memory_review(submission_id: str, payload: ReviewDecision,
                  authorization: str | None = Header(default=None)):
    actor_id = _memory_actor(authorization, reviewer=True)
    try:
        return memory.review_hypothesis(
            submission_id, decision=payload.decision,
            rationale=payload.rationale, checklist=payload.checklist.model_dump(),
            reviewer_id=actor_id,
        )
    except Exception as exc:
        _memory_error(exc)


@app.post("/memory/incidents/{incident_id}/revoke")
def memory_revoke(incident_id: str, payload: Rationale,
                  authorization: str | None = Header(default=None)):
    actor_id = _memory_actor(authorization, reviewer=True)
    try:
        return memory.revoke_confirmation(incident_id, rationale=payload.rationale,
                                          reviewer_id=actor_id)
    except Exception as exc:
        _memory_error(exc)


@app.get("/memory/similar/{run_id}")
def memory_similar(run_id: int, authorization: str | None = Header(default=None)):
    _memory_actor(authorization)
    try:
        incident = investigate_pipeline(run_id)
        if incident is None:
            raise HTTPException(404, "Incident not found")
        return memory.similar_incidents(incident)
    except Exception as exc:
        _memory_error(exc)


@app.post("/memory/matches/{match_id}/reject")
def memory_reject_match(match_id: str, authorization: str | None = Header(default=None)):
    actor_id = _memory_actor(authorization)
    try:
        return memory.reject_match(match_id, actor_id=actor_id)
    except Exception as exc:
        _memory_error(exc)
