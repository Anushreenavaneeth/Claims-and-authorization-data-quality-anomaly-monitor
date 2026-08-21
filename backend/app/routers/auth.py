from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    SetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyTokenResponse,
)
from app.services.auth_service import (
    create_access_token,
    get_user_by_email,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if user is None or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact your administrator.",
        )

    # Log successful login in audit trail
    try:
        audit = AuditLog(
            action="USER_LOGIN",
            performed_by=user.name,
            notes=f"User {user.email} logged in with role {user.role}",
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[AUTH] Audit log notice: {e}")

    token = create_access_token(user)
    user_res = UserResponse.model_validate(user)
    user_res.has_password = True
    return TokenResponse(access_token=token, user=user_res)



@router.get("/verify-token", response_model=VerifyTokenResponse)
def verify_invite_token(
    token: str = Query(..., description="Invite token"),
    db: Session = Depends(get_db),
):
    """Check if an invite token is valid and active."""
    user = db.query(User).filter(User.invite_token == token).first()
    if not user:
        return VerifyTokenResponse(valid=False, message="Invalid or expired invitation token.")

    if user.invite_token_expires_at and user.invite_token_expires_at < datetime.now(timezone.utc):
        return VerifyTokenResponse(valid=False, message="This invitation link has expired. Please request a new invite.")

    return VerifyTokenResponse(valid=True, email=user.email, name=user.name, message="Token is valid.")


@router.post("/set-password", response_model=TokenResponse)
def set_password(payload: SetPasswordRequest, db: Session = Depends(get_db)):
    """Set credentials using invite token, activate account, and log in."""
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )

    user = db.query(User).filter(User.invite_token == payload.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invitation token.",
        )

    if user.invite_token_expires_at and user.invite_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation token has expired.",
        )

    user.password_hash = hash_password(payload.password)
    user.invite_token = None
    user.invite_token_expires_at = None
    user.is_active = True

    audit = AuditLog(
        action="CREDENTIALS_SET",
        performed_by=user.name,
        notes=f"Worker {user.email} successfully set credentials and activated account via email invite.",
    )
    db.add(audit)
    db.commit()
    db.refresh(user)

    token = create_access_token(user)
    user_res = UserResponse.model_validate(user)
    user_res.has_password = True
    return TokenResponse(access_token=token, user=user_res)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    res = UserResponse.model_validate(current_user)
    res.has_password = bool(current_user.password_hash)
    return res


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}
