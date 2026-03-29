from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PrincipalRead(BaseModel):
    user_id: Optional[UUID] = None
    email: str
    role: str
    auth_mode: str


class AuthConfigRead(BaseModel):
    auth_mode: str
    interactive_login: bool
    provider: Optional[str] = None


class AppUserRead(BaseModel):
    id: UUID
    email: str
    display_name: Optional[str] = None
    role: str
    status: str
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AppUserCreate(BaseModel):
    email: str
    display_name: Optional[str] = None
    role: str = "viewer"
    status: str = "ACTIVE"


class AppUserUpdate(BaseModel):
    email: Optional[str] = None
    display_name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
