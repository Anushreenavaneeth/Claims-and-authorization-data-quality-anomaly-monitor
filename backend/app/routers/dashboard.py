"""
Dashboard Router
================
Provides aggregate statistics and trend data for the frontend dashboard.
All data comes from the integration orchestrator's SQLite persistence layer.

GET /api/dashboard/summary
GET /api/anomalies/integrated          (paginated list from unified DB)
GET /api/anomalies/integrated/{record_id}
GET /api/anomalies/integrated/{record_id}/sla
GET /api/anomalies/integrated/{record_id}/recommendation
GET /api/quality
GET /api/root-causes
GET /api/trends
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

# Ensure the project root is on the Python path so integration/ can be imported
# dashboard.py lives at backend/app/routers/ → parents[3] = project root
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.dependencies.auth import get_current_user
from app.models.user import User

try:
    from integration.orchestrator import (
        get_dashboard_summary,
        get_result_by_record_id,
        query_results,
    )
    _INTEGRATION_AVAILABLE = True
except Exception:
    _INTEGRATION_AVAILABLE = False

router = APIRouter(prefix="/api", tags=["Dashboard"])


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _require_integration():
    if not _INTEGRATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Integration layer not available. Run the pipeline first.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard summary
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/dashboard/summary")
def dashboard_summary(_: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Returns aggregated statistics for the main dashboard overview.
    """
    _require_integration()
    return get_dashboard_summary()


# ─────────────────────────────────────────────────────────────────────────────
# Integrated anomaly list
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/anomalies/integrated")
def list_integrated_anomalies(
    dataset:    Optional[str]  = Query(None, description="claims | authorization | pharmacy"),
    severity:   Optional[str]  = Query(None, description="LOW | MEDIUM | HIGH | CRITICAL"),
    sla_status: Optional[str]  = Query(None, description="NORMAL | ELEVATED | AT_RISK | BREACHED"),
    is_anomaly: Optional[bool] = Query(None),
    search:     Optional[str]  = Query(None),
    page:       int            = Query(1, ge=1),
    page_size:  int            = Query(50, ge=1, le=200),
    _:          User           = Depends(get_current_user),
) -> Dict[str, Any]:
    _require_integration()
    return query_results(
        dataset    = dataset,
        severity   = severity,
        sla_status = sla_status,
        is_anomaly = is_anomaly,
        search     = search,
        page       = page,
        page_size  = page_size,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Single integrated anomaly record
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/anomalies/integrated/{record_id}")
def get_integrated_anomaly(
    record_id: str,
    _: User = Depends(get_current_user),
) -> Dict[str, Any]:
    _require_integration()
    result = get_result_by_record_id(record_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found.")
    return result


@router.get("/anomalies/integrated/{record_id}/sla")
def get_sla_for_record(
    record_id: str,
    _: User = Depends(get_current_user),
) -> Dict[str, Any]:
    _require_integration()
    result = get_result_by_record_id(record_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found.")
    return result.get("sla", {})


@router.get("/anomalies/integrated/{record_id}/recommendation")
def get_recommendation_for_record(
    record_id: str,
    _: User = Depends(get_current_user),
) -> Dict[str, Any]:
    _require_integration()
    result = get_result_by_record_id(record_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found.")
    return result.get("rag", {})


# ─────────────────────────────────────────────────────────────────────────────
# Quality endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/quality")
def get_quality_stats(_: User = Depends(get_current_user)) -> Dict[str, Any]:
    _require_integration()
    summary = get_dashboard_summary()
    return {
        "average_quality_score": summary.get("average_quality_score", 0),
        "datasets":              summary.get("datasets", []),
        "total_records":         summary.get("total_records", 0),
        "total_anomalies":       summary.get("total_anomalies", 0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Root causes endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/root-causes")
def get_root_causes(
    dataset:   Optional[str] = Query(None),
    limit:     int           = Query(20, ge=1, le=100),
    _:         User          = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return the most common root causes / rule violations."""
    _require_integration()

    results = query_results(
        dataset    = dataset,
        is_anomaly = True,
        page_size  = 1000,
    )

    rule_counts: Dict[str, int] = {}
    for item in results.get("items", []):
        for rn in item.get("rules", {}).get("rule_names", []):
            rule_counts[rn] = rule_counts.get(rn, 0) + 1

    sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    return {
        "root_causes": [
            {"rule": k, "count": v}
            for k, v in sorted_rules
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
# Trends endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/trends")
def get_trends(
    dataset: Optional[str] = Query(None),
    _:       User          = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return anomaly counts grouped by dataset and severity for trend charts."""
    _require_integration()
    summary = get_dashboard_summary()
    return {
        "datasets":              summary.get("datasets",             []),
        "severity_distribution": summary.get("severity_distribution", {}),
        "sla_distribution":      summary.get("sla_distribution",     {}),
        "total_records":         summary.get("total_records",         0),
        "total_anomalies":       summary.get("total_anomalies",       0),
    }
