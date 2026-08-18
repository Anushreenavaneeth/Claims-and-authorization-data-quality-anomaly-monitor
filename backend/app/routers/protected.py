from fastapi import APIRouter, Depends

from app.dependencies.auth import require_admin, require_worker
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(tags=["Protected"])


@router.get("/admin/dashboard", response_model=UserResponse)
def admin_dashboard(current_user: User = Depends(require_admin)):
    """Admin-only endpoint. Returns current admin user info."""
    return UserResponse.model_validate(current_user)


@router.get("/worker/dashboard", response_model=UserResponse)
def worker_dashboard(current_user: User = Depends(require_worker)):
    """Worker-only endpoint. Returns current worker user info."""
    return UserResponse.model_validate(current_user)
