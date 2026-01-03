"""
Pydantic schemas for Application model.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ApplicationBase(BaseModel):
    """Base schema for Application."""
    name: str
    owner_team: Optional[str] = None
    description: Optional[str] = None
    status: str = "ACTIVE"


class ApplicationCreate(ApplicationBase):
    """Schema for creating an Application."""
    pass


class ApplicationUpdate(BaseModel):
    """Schema for updating an Application."""
    name: Optional[str] = None
    owner_team: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ApplicationResponse(ApplicationBase):
    """Schema for Application response."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
