from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.core import DatabaseInstance, SyncSource
from app.schemas.failover import FailoverResponse

class FailoverService:
    def __init__(self, db: Session):
        self.db = db

    def promote_to_primary(self, new_primary_id: UUID, old_primary_id: Optional[UUID] = None) -> FailoverResponse:
        # 1. Get New Primary
        new_primary = self.db.get(DatabaseInstance, new_primary_id)
        if not new_primary:
            raise ValueError(f"New primary instance {new_primary_id} not found")

        # 2. Update New Primary Role
        new_primary.role = "PRIMARY"
        new_primary.status = "ACTIVE"
        
        updated_sources = 0

        # 3. Handle Old Primary (if known)
        if old_primary_id:
            old_primary = self.db.get(DatabaseInstance, old_primary_id)
            if old_primary:
                old_primary.role = "FAILED" # Or REPLICA if graceful switch
                old_primary.status = "INACTIVE"
                
                # 4. Rebind SyncSources
                # Find all sources using the old primary
                stmt = select(SyncSource).where(SyncSource.database_instance_id == old_primary_id)
                sources = self.db.execute(stmt).scalars().all()
                
                for source in sources:
                    source.database_instance_id = new_primary_id
                    updated_sources += 1

        self.db.commit()
        self.db.refresh(new_primary)
        
        return FailoverResponse(
            success=True,
            message=f"Promoted {new_primary.instance_label} to PRIMARY. Rebound {updated_sources} sync sources.",
            updated_source_count=updated_sources
        )
