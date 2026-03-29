from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func
from app.api.responses import success_response
from app.db.session import get_db
from app.core.security import VIEWER_ROLES, Principal, require_roles
from app.schemas.api import ApiResponse
from app.models.core import SyncRun
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter()

class SyncRunRead(BaseModel):
    id: UUID
    sync_def_id: UUID
    run_type: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    items_processed: int
    items_failed: int
    error_message: Optional[str]

    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=ApiResponse[List[SyncRunRead]])
def list_runs(
    request: Request,
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sync_def_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    run_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = select(SyncRun).order_by(desc(SyncRun.start_time))
    count_query = select(func.count()).select_from(SyncRun)

    if sync_def_id:
        query = query.where(SyncRun.sync_def_id == sync_def_id)
        count_query = count_query.where(SyncRun.sync_def_id == sync_def_id)
    if status:
        query = query.where(SyncRun.status == status)
        count_query = count_query.where(SyncRun.status == status)
    if run_type:
        query = query.where(SyncRun.run_type == run_type)
        count_query = count_query.where(SyncRun.run_type == run_type)

    total = db.execute(count_query).scalar_one()
    query = query.offset(offset).limit(limit)
    result = db.execute(query)
    return success_response(
        request,
        result.scalars().all(),
        meta={"total": total, "limit": limit, "offset": offset},
    )
