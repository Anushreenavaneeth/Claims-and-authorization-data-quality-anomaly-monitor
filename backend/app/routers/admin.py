from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.auth import UserResponse
from app.services.auth_service import hash_password
from app.utils.enums import UserRole

router = APIRouter(prefix="/admin", tags=["Admin"])


class CreateWorkerRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


@router.get("/workers", response_model=list[UserResponse])
def list_workers(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Return all worker accounts."""
    return db.query(User).filter(User.role == UserRole.WORKER).all()


@router.post("/workers", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_worker(
    payload: CreateWorkerRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Create a new worker account. Admin only."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )
    worker = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.WORKER,
        is_active=True,
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


@router.patch("/workers/{worker_id}/deactivate", response_model=UserResponse)
def deactivate_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Deactivate a worker account. Admin only."""
    worker = db.query(User).filter(
        User.id == worker_id,
        User.role == UserRole.WORKER,
    ).first()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    worker.is_active = False
    db.commit()
    db.refresh(worker)
    return worker
