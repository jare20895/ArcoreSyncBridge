from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.core import SyncRun

class RunHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def start_run(self, sync_def_id: UUID, run_type: str) -> SyncRun:
        run = SyncRun(
            id=uuid4(),
            sync_def_id=sync_def_id,
            run_type=run_type,
            status="RUNNING",
            start_time=datetime.utcnow()
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def end_run(self, run_id: UUID, status: str, items_processed: int = 0, items_failed: int = 0, error_message: Optional[str] = None):
        run = self.db.get(SyncRun, run_id)
        if run:
            run.status = status
            run.end_time = datetime.utcnow()
            run.items_processed = items_processed
            run.items_failed = items_failed
            run.error_message = error_message
            self.db.commit()
