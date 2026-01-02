import hashlib
import json
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.core import SyncDefinition, SyncCursor, SharePointConnection, SyncTarget, SyncSource, SyncLedgerEntry
from app.services.sharepoint_content import SharePointContentService
from app.services.graph import GraphClient
from app.services.database import DatabaseClient
import os

class Pusher:
    def __init__(self, db: Session):
        self.db = db

    def run_push(self, sync_def_id: UUID) -> dict:
        """
        Pushes changes from Source Database to SharePoint (Two-Way Sync or One-Way Push).
        Implements Loop Prevention using SyncLedger.
        """
        # 1. Load Definition
        sync_def = self.db.get(SyncDefinition, sync_def_id)
        if not sync_def:
            raise ValueError("Sync definition not found")

        # 2. Resolve Connection & Site
        conn = self.db.query(SharePointConnection).filter(SharePointConnection.status == "ACTIVE").first()
        if not conn:
             raise ValueError("No active SharePoint connection found")

        real_secret = os.environ.get("AZURE_CLIENT_SECRET", "")
        site_id = os.environ.get("SHAREPOINT_SITE_ID", "")
        
        graph = GraphClient(
            tenant_id=conn.tenant_id,
            client_id=conn.client_id,
            client_secret=real_secret, 
            authority_host=conn.authority_host
        )
        content_service = SharePointContentService(graph)

        # 3. Resolve Target List
        target = self.db.execute(select(SyncTarget).where(
            SyncTarget.sync_def_id == sync_def_id,
            SyncTarget.status == "ACTIVE"
        )).scalars().first()
        
        if not target:
             raise ValueError("No active target list found for this definition")

        list_id = str(target.target_list_id)

        # 4. Resolve Source Database Instance
        source_mapping = self.db.execute(select(SyncSource).where(
            SyncSource.sync_def_id == sync_def_id,
            SyncSource.role == "PRIMARY",
            SyncSource.is_enabled == True
        )).scalars().first()
        
        if not source_mapping or not source_mapping.database_instance:
             raise ValueError("No active source database instance found")
        
        db_client = DatabaseClient(source_mapping.database_instance)

        # 5. Get Source Cursor (Watermark)
        cursor_stmt = select(SyncCursor).where(
            SyncCursor.sync_def_id == sync_def_id,
            SyncCursor.cursor_scope == "SOURCE",
            SyncCursor.cursor_type == "TIMESTAMP", # Assuming timestamp strategy
            SyncCursor.source_instance_id == source_mapping.database_instance_id
        )
        cursor = self.db.execute(cursor_stmt).scalars().first()
        last_watermark = cursor.cursor_value if cursor else None

        # 6. Fetch Changed Rows from Source
        # We need the cursor column name. 
        # Ideally mapped via `cursor_column_id` -> Inventory.
        # Fallback: Assume 'updated_at' or check if sync_def has a helper field (not added yet).
        # We'll use 'updated_at' default.
        cursor_col = "updated_at" 
        # In a real impl, we'd lookup `TableColumn` by `cursor_column_id`.
        
        schema_name = sync_def.source_schema or "public"
        table_name = sync_def.source_table_name or sync_def.name
        
        rows = db_client.fetch_changed_rows(schema_name, table_name, cursor_col, last_watermark)
        
        processed_count = 0
        max_cursor_seen = last_watermark

        # Pre-load field mappings
        # Map PG Col -> Target Col
        pg_to_sp_map = {}
        pg_pk_col = "id"
        
        for fm in sync_def.field_mappings:
            if fm.source_column_name and fm.target_column_name:
                pg_to_sp_map[fm.source_column_name] = fm.target_column_name
            if fm.is_key and fm.source_column_name:
                pg_pk_col = fm.source_column_name

        for row in rows:
            # 7. Process Row
            source_id = str(row.get(pg_pk_col))
            id_hash = hashlib.sha256(source_id.encode()).hexdigest()
            
            # Extract content for SP
            sp_fields = {}
            filtered_row_data = {} # For hash
            for pg_col, sp_col in pg_to_sp_map.items():
                val = row.get(pg_col)
                sp_fields[sp_col] = val
                filtered_row_data[pg_col] = val
            
            content_hash = self._compute_content_hash(filtered_row_data)

            # LOOP PREVENTION / LEDGER CHECK
            ledger_entry = self.db.get(SyncLedgerEntry, id_hash)
            
            if ledger_entry:
                # If Provenance is PULL (last write came from SP), we must check if Source changed since then.
                # If Source Timestamp (cursor_col) <= Last Sync TS, then this "change" is just the echo of our PULL.
                # However, we fetched rows WHERE updated_at > last_watermark.
                # If last_watermark was set correctly after PULL, we shouldn't even see this row?
                # Ah, correct. If we update Source during Pull, we should update the SOURCE Cursor too?
                # No, usually we update the Source Row, which bumps 'updated_at'.
                # So the row will appear in `fetch_changed_rows`.
                
                # We check `ledger_entry.last_sync_ts`.
                row_ts = row.get(cursor_col)
                # Ensure row_ts is comparable to last_sync_ts (datetime vs datetime)
                
                if ledger_entry.provenance == "PULL":
                    # Check if hash matches. If hash is same, it's definitely a loop echo.
                    if ledger_entry.content_hash == content_hash:
                        # Skip
                        processed_count += 1
                        # Update max cursor
                        if str(row_ts) > str(max_cursor_seen if max_cursor_seen else ""):
                            max_cursor_seen = str(row_ts)
                        continue
            
            # If we are here, it's a valid Push (New or Update from Source)
            
            if ledger_entry:
                # Update SP Item
                try:
                    content_service.update_item(site_id, list_id, str(ledger_entry.sp_item_id), sp_fields)
                    
                    # Update Ledger
                    ledger_entry.content_hash = content_hash
                    ledger_entry.last_sync_ts = datetime.utcnow()
                    ledger_entry.provenance = "PUSH"
                    ledger_entry.last_source_ts = row_ts if isinstance(row_ts, datetime) else datetime.utcnow() # approx
                except Exception as e:
                    # Log error
                    print(f"Failed to update SP item: {e}")
            else:
                # Create SP Item
                try:
                    sp_id_str = content_service.create_item(site_id, list_id, sp_fields)
                    sp_item_id = int(sp_id_str)
                    
                    # Create Ledger
                    new_entry = SyncLedgerEntry(
                        source_identity_hash=id_hash,
                        source_identity=source_id,
                        source_key_strategy="PRIMARY_KEY",
                        source_instance_id=source_mapping.database_instance_id,
                        sp_list_id=list_id,
                        sp_item_id=sp_item_id,
                        content_hash=content_hash,
                        last_source_ts=row_ts if isinstance(row_ts, datetime) else datetime.utcnow(),
                        last_sync_ts=datetime.utcnow(),
                        provenance="PUSH"
                    )
                    self.db.add(new_entry)
                except Exception as e:
                     print(f"Failed to create SP item: {e}")

            processed_count += 1
            if str(row_ts) > str(max_cursor_seen if max_cursor_seen else ""):
                max_cursor_seen = str(row_ts)

        # 8. Update Cursor
        if max_cursor_seen:
            stmt = insert(SyncCursor).values(
                sync_def_id=sync_def_id,
                cursor_scope="SOURCE",
                cursor_type="TIMESTAMP",
                cursor_value=max_cursor_seen,
                source_instance_id=source_mapping.database_instance_id,
                updated_at=datetime.utcnow()
            ).on_conflict_do_update(
                index_elements=['sync_def_id', 'cursor_scope'],
                set_={
                    "cursor_value": max_cursor_seen,
                    "updated_at": datetime.utcnow()
                }
            )
            self.db.execute(stmt)
            self.db.commit()

        return {
            "processed_count": processed_count,
            "cursor_updated": bool(max_cursor_seen)
        }

    def _compute_content_hash(self, data: Dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
