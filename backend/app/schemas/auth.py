from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    role: str
    is_active: bool = True
    is_archived: bool = False
    has_password: bool = True
    invite_token: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SetPasswordRequest(BaseModel):
    token: str
    password: str


class VerifyTokenResponse(BaseModel):
    valid: bool
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    message: Optional[str] = None
