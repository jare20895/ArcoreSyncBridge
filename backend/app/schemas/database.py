"""
Pydantic schemas for Database model.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class DatabaseBase(BaseModel):
    """Base schema for Database."""
    application_id: UUID
    name: str
    db_type: str = "POSTGRES"
    environment: str
    database_name: str
    status: str = "ACTIVE"


class DatabaseCreate(DatabaseBase):
    """Schema for creating a Database."""
    pass


class DatabaseUpdate(BaseModel):
    """Schema for updating a Database."""
    application_id: Optional[UUID] = None
    name: Optional[str] = None
    db_type: Optional[str] = None
    environment: Optional[str] = None
    database_name: Optional[str] = None
    status: Optional[str] = None


class DatabaseResponse(DatabaseBase):
    """Schema for Database response."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
