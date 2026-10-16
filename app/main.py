from fastapi.middleware.cors import CORSMiddleware
from app.investigator import assess_root_causes
from app.investigator import investigate_pipeline
from fastapi import FastAPI, HTTPException

from app.db import get_failed_pipelines

app = FastAPI(
    title="OpsIntel AI",
    description="Data incident detection and investigation platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
        get_failed_pipelines()
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
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
                    "missing_rows": int(row[4]),
                    "status": row[5],
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
