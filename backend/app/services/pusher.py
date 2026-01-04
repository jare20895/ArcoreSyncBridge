import hashlib
import json
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.core import SyncDefinition, SyncCursor, SharePointConnection, SyncTarget, SyncSource, SyncLedgerEntry
from app.models.inventory import SharePointList, SharePointSite
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

    def _get_content_service(self, connection_id: Optional[UUID], site_id: str) -> tuple[SharePointContentService, str]:
        # Cache key
        cache_key = (connection_id, site_id)
        if cache_key in self._content_service_cache:
            return self._content_service_cache[cache_key]

        real_secret = os.environ.get("AZURE_CLIENT_SECRET", "")
        
        if connection_id:
            conn = self.db.get(SharePointConnection, connection_id)
        else:
            # Fallback to finding ANY active connection if none specified (dangerous but maybe needed for legacy)
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
        
        target_map = {str(t.target_list_id): t for t in targets}
        
        # Fallback: If no explicit SyncTargets but we have a default target_list_id
        if not targets and sync_def.target_list_id:
            # Auto-resolve connection context from Inventory
            sp_list = self.db.get(SharePointList, sync_def.target_list_id)
            if sp_list:
                sp_site = self.db.get(SharePointSite, sp_list.site_id)
                if sp_site:
                    # Create a virtual/transient SyncTarget for this run
                    virtual_target = SyncTarget(
                        sync_def_id=sync_def_id,
                        target_list_id=sync_def.target_list_id,
                        sharepoint_connection_id=sp_site.connection_id,
                        site_id=sp_site.site_id,
                        is_default=True
                    )
                    targets = [virtual_target]
                    target_map[str(sync_def.target_list_id)] = virtual_target

        if not targets:
             raise ValueError("No active target lists found for this definition")
        
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
        
        db_instance = None
        
        if source_mapping:
            db_instance = source_mapping.database_instance
        elif sync_def.source_table_id:
            # Fallback: Infer instance from Source Table ID
            from app.models.inventory import DatabaseTable
            from app.models.core import DatabaseInstance
            
            table = self.db.get(DatabaseTable, sync_def.source_table_id)
            if table:
                # Find an active instance for this table's database
                instance_stmt = select(DatabaseInstance).where(
                    DatabaseInstance.database_id == table.database_id,
                    DatabaseInstance.status == "ACTIVE"
                ).order_by(DatabaseInstance.priority) # Prioritize lower number (1 = primary)
                
                db_instance = self.db.execute(instance_stmt).scalars().first()
        
        if not db_instance:
             raise ValueError("No active source database instance found")
        
        db_client = DatabaseClient(db_instance)

        # 5. Get Source Cursor (Watermark)
        cursor_stmt = select(SyncCursor).where(
            SyncCursor.sync_def_id == sync_def_id,
            SyncCursor.cursor_scope == "SOURCE",
            SyncCursor.cursor_type == "TIMESTAMP", # Assuming timestamp strategy
            SyncCursor.source_instance_id == db_instance.id
        )
        cursor = self.db.execute(cursor_stmt).scalars().first()
        last_watermark = cursor.cursor_value if cursor else None

        # 6. Fetch Changed Rows from Source
        cursor_col = "updated_at" 
        schema_name = sync_def.source_schema or "public"
        table_name = sync_def.source_table_name or sync_def.name
        
        # If table name matches the definition name (e.g. "Sync TableA"), we might need to resolve the real table name
        # The DatabaseClient expects the real table name. 
        # Ideally sync_def.source_table_name is populated. 
        # If not, and we have a source_table_id, fetch it.
        if not sync_def.source_table_name and sync_def.source_table_id:
             from app.models.inventory import DatabaseTable
             tbl = self.db.get(DatabaseTable, sync_def.source_table_id)
             if tbl:
                 table_name = tbl.table_name
                 schema_name = tbl.schema_name

        print(f"[DEBUG] Fetching changed rows from {schema_name}.{table_name} WHERE {cursor_col} > {last_watermark}")
        rows = db_client.fetch_changed_rows(schema_name, table_name, cursor_col, last_watermark)
        print(f"[DEBUG] Found {len(rows)} changed rows to process")

        processed_count = 0
        max_cursor_seen = last_watermark

        # Pre-load field mappings with directional filtering
        # Map PG Col -> Target Col
        pg_to_sp_map = {}
        pg_pk_col = "id"

        for fm in sync_def.field_mappings:
            # Skip PULL_ONLY fields in push sync (they should only sync from SharePoint to Database)
            if fm.sync_direction == "PULL_ONLY":
                continue

            # Phase 6: System Field Safety Check
            # System fields are SharePoint readonly metadata (ID, Created, Modified, etc.)
            # They should never be written to SharePoint, even if accidentally set to BIDIRECTIONAL
            if fm.is_system_field:
                print(f"[WARN] Skipping system field '{fm.target_column_name}' in push sync (readonly metadata)")
                continue

            if fm.source_column_name and fm.target_column_name:
                pg_to_sp_map[fm.source_column_name] = fm.target_column_name
            if fm.is_key and fm.source_column_name:
                pg_pk_col = fm.source_column_name

        print(f"[DEBUG] Field Mappings: {len(pg_to_sp_map)} fields mapped for PUSH (excluding PULL_ONLY). PK: {pg_pk_col}")

        failed_count = 0
        success_count = 0

        for row in rows:
            # 7. Process Row
            source_id = str(row.get(pg_pk_col))
            id_hash = hashlib.sha256(source_id.encode()).hexdigest()
            
            # Extract content for SP with type serialization
            sp_fields = {}
            filtered_row_data = {} # For hash
            for pg_col, sp_col in pg_to_sp_map.items():
                val = row.get(pg_col)
                # Serialize Python types to SharePoint/JSON-compatible types
                serialized_val = self._serialize_value_for_sharepoint(val)
                sp_fields[sp_col] = serialized_val
                filtered_row_data[pg_col] = val
            
            # If no fields mapped, we can't sync content (unless we just want to create empty placeholders, which is rare)
            if not sp_fields:
                print(f"[WARN] No fields mapped for row {source_id}. Skipping sync.")
                failed_count += 1
                continue

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
                failed_count += 1
                continue

            # Validate List Status in Inventory
            # We need to check if the underlying SharePointList is marked DELETED
            # This prevents writing to recycled/stale lists if the user hasn't updated the definition
            sp_list_record = self.db.get(SharePointList, target_obj.target_list_id)
            if sp_list_record and sp_list_record.status == 'DELETED':
                print(f"[ERROR] Target list '{sp_list_record.display_name}' ({target_list_id}) is marked DELETED in inventory. Please update the Sync Definition to point to the new list.")
                failed_count += 1
                continue

            # Resolve the actual SharePoint GUID for API calls (not the database UUID)
            if not sp_list_record:
                print(f"[ERROR] Target list {target_list_id} not found in inventory. Cannot determine SharePoint GUID.")
                failed_count += 1
                continue

            sp_list_guid = sp_list_record.list_id  # This is the actual SharePoint GUID

            try:
                content_service, site_id = self._get_content_service(target_obj.sharepoint_connection_id, target_obj.site_id)
            except Exception as e:
                print(f"Failed to get content service for target {target_list_id}: {e}")
                failed_count += 1
                continue

            # LOOP PREVENTION / LEDGER CHECK
            ledger_entry = self.db.get(SyncLedgerEntry, (sync_def_id, id_hash))
            
            if ledger_entry:
                # If Provenance is PULL (last write came from SP), we must check if Source changed since then.
                if ledger_entry.provenance == "PULL":
                    # Check if hash matches. If hash is same, it's definitely a loop echo.
                    if ledger_entry.content_hash == content_hash:
                        # Skip
                        # Update max cursor
                        if str(row_ts) > str(max_cursor_seen if max_cursor_seen else ""):
                            max_cursor_seen = str(row_ts)
                        continue
            
            # If we are here, it's a valid Push (New or Update from Source)
            
            if ledger_entry:
                # Update SP Item
                try:
                    content_service.update_item(site_id, sp_list_guid, str(ledger_entry.sp_item_id), sp_fields)
                    
                    # Update Ledger
                    ledger_entry.content_hash = content_hash
                    ledger_entry.last_sync_ts = datetime.utcnow()
                    ledger_entry.provenance = "PUSH"
                    ledger_entry.last_source_ts = row_ts if isinstance(row_ts, datetime) else datetime.utcnow() # approx
                    success_count += 1
                    # Only advance cursor on successful update
                    if str(row_ts) > str(max_cursor_seen if max_cursor_seen else ""):
                        max_cursor_seen = str(row_ts)
                except Exception as e:
                    # Log error
                    print(f"Failed to update SP item: {e}")
                    failed_count += 1
            else:
                # Create SP Item
                try:
                    sp_id_str = content_service.create_item(site_id, sp_list_guid, sp_fields)
                    if sp_id_str:
                        sp_item_id = int(sp_id_str)

                        # Create Ledger
                        new_entry = SyncLedgerEntry(
                            sync_def_id=sync_def_id,
                            source_identity_hash=id_hash,
                            source_identity=source_id,
                            source_key_strategy="PRIMARY_KEY",
                            source_instance_id=db_instance.id,
                            sp_list_id=sp_list_guid,  # Store SharePoint GUID in ledger
                            sp_item_id=sp_item_id,
                            content_hash=content_hash,
                            last_source_ts=row_ts if isinstance(row_ts, datetime) else datetime.utcnow(),
                            last_sync_ts=datetime.utcnow(),
                            provenance="PUSH"
                        )
                        self.db.add(new_entry)
                        success_count += 1
                        # Only advance cursor on successful create
                        if str(row_ts) > str(max_cursor_seen if max_cursor_seen else ""):
                            max_cursor_seen = str(row_ts)
                    else:
                        print(f"Graph API returned no ID for created item. Payload: {sp_fields}")
                        failed_count += 1
                except Exception as e:
                     print(f"Failed to create SP item: {e}")
                     failed_count += 1

            processed_count += 1

        # 8. Update Cursor
        if max_cursor_seen:
            # Check for existing cursor
            cursor_stmt = select(SyncCursor).where(
                SyncCursor.sync_def_id == sync_def_id,
                SyncCursor.cursor_scope == "SOURCE",
                SyncCursor.source_instance_id == db_instance.id
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
                    source_instance_id=db_instance.id,
                    updated_at=datetime.utcnow()
                )
                self.db.add(new_cursor)
            
            self.db.commit()

        return {
            "processed_count": processed_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "cursor_updated": bool(max_cursor_seen)
        }

    def _serialize_value_for_sharepoint(self, value: Any) -> Any:
        """
        Convert Python types to SharePoint/JSON-compatible types.
        """
        if value is None:
            return None
        elif isinstance(value, datetime):
            # SharePoint expects ISO 8601 format with timezone
            return value.isoformat()
        elif isinstance(value, date):
            # Convert date to datetime at midnight, then to ISO 8601
            return datetime.combine(value, datetime.min.time()).isoformat()
        elif isinstance(value, Decimal):
            # Convert Decimal to float for JSON serialization
            return float(value)
        elif isinstance(value, UUID):
            return str(value)
        else:
            return value

    def _compute_content_hash(self, data: Dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
