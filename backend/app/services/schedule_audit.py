from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.core import ScheduledSyncAudit


class ScheduleAuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_skip(self, sync_def_id: UUID, reason: str):
        """Log when a scheduled sync is skipped."""
        audit = ScheduledSyncAudit(
            id=uuid4(),
            sync_def_id=sync_def_id,
            periodic_task_id=0,  # Unknown at skip time
            scheduled_time=datetime.utcnow(),
            status="SKIPPED",
            skip_reason=reason
        )
        self.db.add(audit)
        self.db.commit()

    def get_recent_audits(self, sync_def_id: UUID, limit: int = 50):
        """Get recent audit logs for a sync definition."""
        stmt = select(ScheduledSyncAudit).where(
            ScheduledSyncAudit.sync_def_id == sync_def_id
        ).order_by(desc(ScheduledSyncAudit.created_at)).limit(limit)
        return self.db.execute(stmt).scalars().all()
