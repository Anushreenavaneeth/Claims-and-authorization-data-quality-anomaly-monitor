"""
Pipeline Router
===============
Triggers the integration orchestrator to process datasets on demand.

POST /api/process          — process one or all datasets
GET  /api/process/status   — check whether the DB has data
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.dependencies.auth import require_admin
from app.models.user import User

try:
    from integration.orchestrator import process_dataset, process_all, get_dashboard_summary
    _INTEGRATION_AVAILABLE = True
except Exception as _ie:
    _INTEGRATION_AVAILABLE = False
    _IMPORT_ERROR = str(_ie)

router = APIRouter(prefix="/api", tags=["Pipeline"])


class ProcessRequest(BaseModel):
    dataset:      Optional[str] = None   # "claims" | "authorization" | "pharmacy" | None=all
    max_records:  Optional[int] = None   # limit for testing
    anomalies_only: bool        = False  # only persist anomalous records


@router.post("/process")
def trigger_pipeline(
    request:          ProcessRequest,
    background_tasks: BackgroundTasks,
    _:                User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Trigger the integration pipeline.
    Runs in the background; returns immediately with a status message.
    Admin role required.
    """
    if not _INTEGRATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=f"Integration layer not importable: {_IMPORT_ERROR}",
        )

    dataset = request.dataset

    if dataset and dataset.lower() not in ("claims", "authorization", "pharmacy"):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown dataset '{dataset}'. Use: claims, authorization, pharmacy",
        )

    def _run():
        if dataset:
            process_dataset(dataset.lower(), max_records=request.max_records, anomalies_only=request.anomalies_only)
        else:
            process_all(max_records_per_dataset=request.max_records)

    background_tasks.add_task(_run)

    return {
        "status":  "started",
        "dataset": dataset or "all",
        "message": f"Pipeline started for '{dataset or 'all'}'. Check /api/dashboard/summary for results.",
    }


@router.get("/process/status")
def pipeline_status(_: User = Depends(require_admin)) -> Dict[str, Any]:
    """Check whether processed data exists."""
    if not _INTEGRATION_AVAILABLE:
        return {"status": "unavailable", "records": 0}
    try:
        summary = get_dashboard_summary()
        return {
            "status":  "ready" if summary["total_records"] > 0 else "empty",
            "records": summary["total_records"],
        }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
