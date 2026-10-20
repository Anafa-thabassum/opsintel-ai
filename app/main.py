import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
