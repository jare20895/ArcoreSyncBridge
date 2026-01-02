from typing import Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.core import SyncLedgerEntry, SyncCursor, MoveAuditLog

class LedgerService:
    def __init__(self, db: Session):
        self.db = db

    def log_move(self, source_identity_hash: str, from_list_id: str, to_list_id: str, status: str = "SUCCESS", details: str = None, sync_def_id: Optional[UUID] = None):
        audit_entry = MoveAuditLog(
            source_identity_hash=source_identity_hash,
            from_list_id=from_list_id,
            to_list_id=to_list_id,
            status=status,
            details=details,
            sync_def_id=sync_def_id
        )
        self.db.add(audit_entry)
        self.db.commit()

    def get_entry(self, sync_def_id: UUID, source_identity_hash: str) -> Optional[SyncLedgerEntry]:
        return self.db.get(SyncLedgerEntry, (sync_def_id, source_identity_hash))

    def record_entry(self, entry: SyncLedgerEntry) -> SyncLedgerEntry:
        existing = self.db.get(SyncLedgerEntry, (entry.sync_def_id, entry.source_identity_hash))
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

    def get_cursor(self, sync_def_id: UUID, cursor_scope: str, source_instance_id: Optional[UUID] = None, target_list_id: Optional[UUID] = None) -> Optional[SyncCursor]:
        stmt = select(SyncCursor).where(
            SyncCursor.sync_def_id == sync_def_id,
            SyncCursor.cursor_scope == cursor_scope
        )
        if source_instance_id:
            stmt = stmt.where(SyncCursor.source_instance_id == source_instance_id)
        if target_list_id:
             stmt = stmt.where(SyncCursor.target_list_id == target_list_id)
             
        return self.db.execute(stmt).scalars().first()

    def update_cursor(self, sync_def_id: UUID, cursor_scope: str, cursor_type: str, cursor_value: str, source_instance_id: Optional[UUID] = None, target_list_id: Optional[UUID] = None):
        cursor = self.get_cursor(sync_def_id, cursor_scope, source_instance_id, target_list_id)
        
        if cursor:
            cursor.cursor_value = cursor_value
            cursor.updated_at = datetime.utcnow()
            # Ensure optional fields match what we expect, though get_cursor filtered by them
            if source_instance_id:
                cursor.source_instance_id = source_instance_id
            if target_list_id:
                cursor.target_list_id = target_list_id
        else:
            cursor = SyncCursor(
                sync_def_id=sync_def_id,
                cursor_scope=cursor_scope,
                cursor_type=cursor_type,
                cursor_value=cursor_value,
                source_instance_id=source_instance_id,
                target_list_id=target_list_id,
                updated_at=datetime.utcnow()
            )
            self.db.add(cursor)
        
        self.db.commit()
        return cursor
