from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.api.endpoints.database_instances import get_db
from app.models.core import SyncRun
from pydantic import BaseModel
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

    class Config:
        from_attributes = True

@router.get("/", response_model=List[SyncRunRead])
def list_runs(
    skip: int = 0,
    limit: int = 50,
    sync_def_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    query = select(SyncRun).order_by(desc(SyncRun.start_time))
    
    if sync_def_id:
        query = query.where(SyncRun.sync_def_id == sync_def_id)
        
    query = query.offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()
