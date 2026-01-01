from typing import Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.core import SyncLedgerEntry, SyncCursor

class LedgerService:
    def __init__(self, db: Session):
        self.db = db

    def get_entry(self, source_identity_hash: str) -> Optional[SyncLedgerEntry]:
        return self.db.get(SyncLedgerEntry, source_identity_hash)

    def record_entry(self, entry: SyncLedgerEntry) -> SyncLedgerEntry:
        existing = self.db.get(SyncLedgerEntry, entry.source_identity_hash)
        if existing:
            existing.sp_list_id = entry.sp_list_id
            existing.sp_item_id = entry.sp_item_id
            existing.content_hash = entry.content_hash
            existing.last_sync_ts = entry.last_sync_ts
            existing.provenance = entry.provenance
            # source_instance_id and identity don't change for the same hash usually
        else:
            self.db.add(entry)
        
        self.db.commit()
        if existing:
            self.db.refresh(existing)
            return existing
        else:
            self.db.refresh(entry)
            return entry

class CursorService:
    def __init__(self, db: Session):
        self.db = db

    def get_cursor(self, sync_def_id: UUID, cursor_scope: str) -> Optional[SyncCursor]:
        return self.db.get(SyncCursor, (sync_def_id, cursor_scope))

    def update_cursor(self, sync_def_id: UUID, cursor_scope: str, cursor_type: str, cursor_value: str, source_instance_id: Optional[UUID] = None):
        cursor = self.db.get(SyncCursor, (sync_def_id, cursor_scope))
        if cursor:
            cursor.cursor_value = cursor_value
            cursor.updated_at = datetime.utcnow()
            if source_instance_id:
                cursor.source_instance_id = source_instance_id
        else:
            cursor = SyncCursor(
                sync_def_id=sync_def_id,
                cursor_scope=cursor_scope,
                cursor_type=cursor_type,
                cursor_value=cursor_value,
                source_instance_id=source_instance_id
            )
            self.db.add(cursor)
        
        self.db.commit()
        return cursor
