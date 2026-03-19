from uuid import UUID
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.security import OPERATOR_ROLES, require_roles
from app.db.session import SessionLocal
from app.services.schedule_service import ScheduleService
from app.services.schedule_audit import ScheduleAuditService


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Schemas
class ScheduleConfig(BaseModel):
    schedule_type: str = Field(..., pattern="^(INTERVAL|CRON)$")
    interval_seconds: Optional[int] = Field(None, ge=60)
    cron_expression: Optional[str] = None
    timezone: str = "UTC"


class ScheduleResponse(BaseModel):
    message: str
    next_run: Optional[datetime] = None


class AuditLogResponse(BaseModel):
    id: UUID
    sync_def_id: UUID
    scheduled_time: datetime
    actual_start_time: Optional[datetime]
    completion_time: Optional[datetime]
    status: str
    skip_reason: Optional[str]
    sync_run_id: Optional[UUID]

    class Config:
        from_attributes = True


# Endpoints
@router.post("/{sync_def_id}/enable", response_model=ScheduleResponse)
def enable_schedule(
    sync_def_id: UUID,
    config: ScheduleConfig,
    _: None = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db)
):
    """Enable scheduled sync for a sync definition."""
    service = ScheduleService(db)
    try:
        return service.enable_schedule(
            sync_def_id,
            config.schedule_type,
            config.interval_seconds,
            config.cron_expression,
            config.timezone
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{sync_def_id}/disable", response_model=ScheduleResponse)
def disable_schedule(
    sync_def_id: UUID,
    _: None = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
):
    """Disable scheduled sync for a sync definition."""
    service = ScheduleService(db)
    try:
        return service.disable_schedule(sync_def_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{sync_def_id}")
def delete_schedule(
    sync_def_id: UUID,
    _: None = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
):
    """Delete schedule for a sync definition."""
    service = ScheduleService(db)
    try:
        return service.delete_schedule(sync_def_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{sync_def_id}/audit", response_model=List[AuditLogResponse])
def get_schedule_audit(
    sync_def_id: UUID,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get schedule audit logs for a sync definition."""
    service = ScheduleAuditService(db)
    return service.get_recent_audits(sync_def_id, limit)
