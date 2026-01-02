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

from app.services.sharding import ShardingEvaluator

class Pusher:
    def __init__(self, db: Session):
        self.db = db
        self._conn_cache = {}
        self._content_service_cache = {}

    def _get_content_service(self, target: SyncTarget) -> tuple[SharePointContentService, str]:
        # Cache key could be connection_id + site_id
        conn_id = target.sharepoint_connection_id
        # Use target site_id or fallback. We need this for the key too if connection is reused across sites.
        real_secret = os.environ.get("AZURE_CLIENT_SECRET", "")
        site_id = target.site_id or os.environ.get("SHAREPOINT_SITE_ID", "")
        
        if not conn_id:
             cache_key = ("DEFAULT", site_id)
        else:
             cache_key = (conn_id, site_id)
             
        if cache_key in self._content_service_cache:
            return self._content_service_cache[cache_key]

        # Resolve Connection
        if conn_id:
            conn = self.db.get(SharePointConnection, conn_id)
        else:
            conn = self.db.query(SharePointConnection).filter(SharePointConnection.status == "ACTIVE").first()

        if not conn:
             raise ValueError("No active SharePoint connection found")

        graph = GraphClient(
            tenant_id=conn.tenant_id,
            client_id=conn.client_id,
            client_secret=real_secret, 
            authority_host=conn.authority_host
        )
        service = SharePointContentService(graph)
        
        self._content_service_cache[cache_key] = (service, site_id)
        return service, site_id

    def run_push(self, sync_def_id: UUID) -> dict:
        """
        Pushes changes from Source Database to SharePoint (Two-Way Sync or One-Way Push).
        Implements Loop Prevention using SyncLedger.
        """
        # 1. Load Definition
        sync_def = self.db.get(SyncDefinition, sync_def_id)
        if not sync_def:
            raise ValueError("Sync definition not found")

        # 2. Resolve Targets
        targets = self.db.execute(select(SyncTarget).where(
            SyncTarget.sync_def_id == sync_def_id,
            SyncTarget.status == "ACTIVE"
        )).scalars().all()
        
        if not targets:
             raise ValueError("No active target lists found for this definition")
        
        target_map = {str(t.target_list_id): t for t in targets}
        default_target = next((t for t in targets if t.is_default), targets[0])

        # Setup Sharding if needed
        sharding_evaluator = None
        if sync_def.target_strategy == "CONDITIONAL":
            sharding_evaluator = ShardingEvaluator(sync_def.sharding_policy)

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
        cursor_col = "updated_at" 
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

            # Extract Timestamp
            row_ts = row.get(cursor_col)

            # Determine Target
            target_list_id = None
            if sharding_evaluator:
                shard_uuid = sharding_evaluator.evaluate(row)
                if shard_uuid:
                    target_list_id = str(shard_uuid)
            
            if not target_list_id:
                target_list_id = str(default_target.target_list_id)

            # Resolve Target Context
            target_obj = target_map.get(target_list_id)
            if not target_obj:
                print(f"Target list {target_list_id} determined but not found in active targets. Skipping.")
                continue

            try:
                content_service, site_id = self._get_content_service(target_obj)
            except Exception as e:
                print(f"Failed to get content service for target {target_list_id}: {e}")
                continue

            # LOOP PREVENTION / LEDGER CHECK
            ledger_entry = self.db.get(SyncLedgerEntry, (sync_def_id, id_hash))
            
            if ledger_entry:
                # If Provenance is PULL (last write came from SP), we must check if Source changed since then.
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
                    content_service.update_item(site_id, target_list_id, str(ledger_entry.sp_item_id), sp_fields)
                    
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
                    sp_id_str = content_service.create_item(site_id, target_list_id, sp_fields)
                    sp_item_id = int(sp_id_str)
                    
                    # Create Ledger
                    new_entry = SyncLedgerEntry(
                        sync_def_id=sync_def_id,
                        source_identity_hash=id_hash,
                        source_identity=source_id,
                        source_key_strategy="PRIMARY_KEY",
                        source_instance_id=source_mapping.database_instance_id,
                        sp_list_id=target_list_id,
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
            # Check for existing cursor
            cursor_stmt = select(SyncCursor).where(
                SyncCursor.sync_def_id == sync_def_id,
                SyncCursor.cursor_scope == "SOURCE",
                SyncCursor.source_instance_id == source_mapping.database_instance_id
            )
            cursor = self.db.execute(cursor_stmt).scalars().first()
            
            if cursor:
                cursor.cursor_value = max_cursor_seen
                cursor.updated_at = datetime.utcnow()
                self.db.add(cursor)
            else:
                new_cursor = SyncCursor(
                    sync_def_id=sync_def_id,
                    cursor_scope="SOURCE",
                    cursor_type="TIMESTAMP",
                    cursor_value=max_cursor_seen,
                    source_instance_id=source_mapping.database_instance_id,
                    updated_at=datetime.utcnow()
                )
                self.db.add(new_cursor)
            
            self.db.commit()

        return {
            "processed_count": processed_count,
            "cursor_updated": bool(max_cursor_seen)
        }

    def _compute_content_hash(self, data: Dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
