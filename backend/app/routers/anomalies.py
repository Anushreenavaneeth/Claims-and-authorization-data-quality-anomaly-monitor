from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.anomaly import Anomaly
from app.models.user import User
from app.realtime.manager import anomaly_manager
from app.schemas.anomaly import (
    AnomalyCreate,
    AnomalyListResponse,
    AnomalyResponse,
    AnomalyStatusUpdate,
)
from app.utils.enums import AnomalySeverity, AnomalyStatus, SourceDataset

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


# ── List anomalies with filters + pagination ──────────────────────────────

@router.get("", response_model=AnomalyListResponse)
def list_anomalies(
    source:    Optional[SourceDataset]   = Query(None),
    severity:  Optional[AnomalySeverity] = Query(None),
    status_:   Optional[AnomalyStatus]   = Query(None, alias="status"),
    search:    Optional[str]             = Query(None, description="Search record_id, anomaly_type, or affected_field"),
    page:      int                       = Query(1, ge=1),
    page_size: int                       = Query(20, ge=1, le=100),
    db:        Session                   = Depends(get_db),
    _:         User                      = Depends(get_current_user),
):
    q = db.query(Anomaly)

    if source:
        q = q.filter(Anomaly.source_dataset == source)
    if severity:
        q = q.filter(Anomaly.severity == severity)
    if status_:
        q = q.filter(Anomaly.status == status_)
    if search:
        term = f"%{search}%"
        q = q.filter(
            Anomaly.record_id.ilike(term)
            | Anomaly.anomaly_type.ilike(term)
            | Anomaly.affected_field.ilike(term)
        )

    total = q.count()
    items = (
        q.order_by(Anomaly.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AnomalyListResponse(total=total, page=page, page_size=page_size, items=items)


# ── Single anomaly ────────────────────────────────────────────────────────

@router.get("/{anomaly_id}", response_model=AnomalyResponse)
def get_anomaly(
    anomaly_id: str,
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found.")
    return anomaly


# ── Update status ─────────────────────────────────────────────────────────

@router.patch("/{anomaly_id}/status", response_model=AnomalyResponse)
async def update_anomaly_status(
    anomaly_id: str,
    payload:    AnomalyStatusUpdate,
    db:         Session = Depends(get_db),
    _:          User    = Depends(get_current_user),
):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found.")

    anomaly.status = payload.status
    db.commit()
    db.refresh(anomaly)

    # Broadcast status change to all WebSocket clients
    await anomaly_manager.broadcast_status_change(anomaly_id, payload.status.value)

    return anomaly


# ── Trigger pipeline re-run (stub — ETL team implements the actual logic) ─

@router.post("/{anomaly_id}/rerun")
def trigger_rerun(
    anomaly_id: str,
    db:         Session = Depends(get_db),
    _:          User    = Depends(require_admin),
):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found.")

    # ETL team hooks into this endpoint to trigger reprocessing
    return {"message": f"Re-run triggered for anomaly {anomaly_id}", "anomaly_id": anomaly_id}


# ── Admin: create anomaly manually (for testing / ML ingestion) ───────────

@router.post("", response_model=AnomalyResponse, status_code=status.HTTP_201_CREATED)
async def create_anomaly(
    payload: AnomalyCreate,
    db:      Session = Depends(get_db),
    _:       User    = Depends(require_admin),
):
    anomaly = Anomaly(**payload.model_dump())
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)

    # Broadcast to WebSocket clients immediately
    await anomaly_manager.broadcast_anomaly(
        AnomalyResponse.model_validate(anomaly).model_dump(mode="json")
    )

    return anomaly


# ── WebSocket endpoint ────────────────────────────────────────────────────

@router.websocket("/ws")
async def anomaly_websocket(websocket: WebSocket):
    """
    Frontend connects here to receive real-time anomaly events.
    Message types emitted:
      { "type": "NEW_ANOMALY",    "data": AnomalyResponse }
      { "type": "STATUS_CHANGED", "data": { "id": str, "status": str } }
      { "type": "PING" }
    """
    await anomaly_manager.connect(websocket)
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "CONNECTED",
            "data": {"connections": anomaly_manager.connection_count},
        })
        while True:
            # Keep alive — client can send "PING" to check connection
            msg = await websocket.receive_text()
            if msg == "PING":
                await websocket.send_json({"type": "PONG"})
    except WebSocketDisconnect:
        anomaly_manager.disconnect(websocket)
