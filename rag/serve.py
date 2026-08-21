"""
RAG Microservice — HTTP interface for the RAG pipeline.

Runs on http://localhost:8001 (Python 3.11).

Endpoints:
    GET  /health          → liveness check
    POST /recommend       → run full RAG pipeline for one anomaly record
"""

import sys
import os
from pathlib import Path

# Ensure the repo root is on sys.path so `rag.*` imports resolve whether
# this file is run as `python rag/serve.py` or `python -m rag.serve`.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import traceback
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional

from rag.pipeline.pipeline import RAGPipeline

# ─────────────────────────────────────────────────────────────────────────────
# Pipeline — initialised once at startup (loads embeddings once)
# ─────────────────────────────────────────────────────────────────────────────

pipeline: Optional[RAGPipeline] = None
init_error: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the RAG pipeline on startup; nothing to tear down."""
    global pipeline, init_error
    try:
        pipeline = RAGPipeline()
        print("RAG pipeline ready.")
    except Exception as exc:  # noqa: BLE001
        init_error = str(exc)
        print(f"WARNING: RAG pipeline failed to initialise: {exc}")
    yield  # server runs here


# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="RAG Recommendation Microservice",
    version="1.0.0",
    description="Standalone RAG service: vector retrieval → XAI → root cause → recommendation.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────


class RecommendRequest(BaseModel):
    """One anomaly record — same shape as authorization_anomalies_for_rag.json entries."""

    model_config = {"extra": "allow"}  # accept any extra fields the caller sends

    dataset_type: str
    record_id: str


class HealthResponse(BaseModel):
    status: str          # "ready" | "degraded"
    error: Optional[str] = None


class RecommendResponse(BaseModel):
    record_id: str
    dataset_type: str
    admin_summary: str
    root_cause: Dict[str, Any]
    employee_action: str
    priority: str
    rag_available: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse)
def health():
    if pipeline is None:
        return HealthResponse(status="degraded", error=init_error)
    return HealthResponse(status="ready", error=None)


@app.post("/recommend", response_model=RecommendResponse)
def recommend(body: RecommendRequest):
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail=f"RAG pipeline not ready: {init_error}",
        )

    # Convert Pydantic model → plain dict so the pipeline receives all fields
    anomaly_record: Dict[str, Any] = body.model_dump()

    try:
        result = pipeline.process_single(anomaly_record)
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {exc}",
        ) from exc

    recommendation = result.get("recommendation", {})

    return RecommendResponse(
        record_id=result.get("record_id", body.record_id),
        dataset_type=result.get("dataset_type", body.dataset_type),
        admin_summary=recommendation.get("admin_summary", ""),
        root_cause=recommendation.get("root_cause", {}),
        employee_action=recommendation.get("employee_action", ""),
        priority=recommendation.get("priority", "Medium"),
        rag_available=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "rag.serve:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
    )
