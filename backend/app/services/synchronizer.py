import hashlib
import json
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from app.models.core import SyncDefinition, SyncCursor, SharePointConnection, SyncTarget, SyncSource, SyncLedgerEntry
from app.services.sharepoint_content import SharePointContentService
from app.services.graph import GraphClient
from app.services.database import DatabaseClient
import os

class Synchronizer:
    def __init__(self, db: Session):
        self.db = db

    def run_ingress(self, sync_def_id: UUID) -> dict:
        """
        Ingests changes from SharePoint for the given sync definition (Two-Way Sync).
        Persists the new delta token.
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

        # 5. Get Current Cursor (Delta Token)
        cursor_stmt = select(SyncCursor).where(
            SyncCursor.sync_def_id == sync_def_id,
            SyncCursor.cursor_scope == "TARGET",
            SyncCursor.cursor_type == "DELTA_TOKEN",
            SyncCursor.target_list_id == target.target_list_id
        )
        cursor = self.db.execute(cursor_stmt).scalars().first()
        current_token = cursor.cursor_value if cursor else None

        # 6. Fetch Changes
        changes, new_token = content_service.get_list_changes(site_id, list_id, current_token)

        # 7. Process Changes
        processed_count = self._process_changes(sync_def, db_client, changes, list_id, source_mapping.database_instance_id)

        # 8. Persist New Token
        if new_token:
            if cursor:
                cursor.cursor_value = new_token
                cursor.updated_at = datetime.utcnow()
                self.db.add(cursor)
            else:
                new_cursor = SyncCursor(
                    sync_def_id=sync_def_id,
                    cursor_scope="TARGET",
                    cursor_type="DELTA_TOKEN",
                    cursor_value=new_token,
                    target_list_id=target.target_list_id,
                    updated_at=datetime.utcnow()
                )
                self.db.add(new_cursor)
            self.db.commit()

        return {
            "processed_count": processed_count,
            "new_token_persisted": bool(new_token)
        }

    def _process_changes(self, sync_def: SyncDefinition, db_client: DatabaseClient, changes: List[Dict], list_id: str, instance_id: UUID) -> int:
        count = 0
        schema_name = sync_def.source_schema or "public"
        table_name = sync_def.source_table_name or sync_def.name # Fallback to Def Name if not set
        
        # Pre-load field mappings
        # Map InternalName -> (SourceColName, TransformRule)
        sp_to_pg_map = {}
        pg_pk_col = "id" # Default
        
        for fm in sync_def.field_mappings:
            if fm.target_column_name and fm.source_column_name:
                sp_to_pg_map[fm.target_column_name] = fm.source_column_name
            if fm.is_key and fm.source_column_name:
                pg_pk_col = fm.source_column_name

        for change in changes:
            sp_item_id = change.get("id") # String usually
            if not sp_item_id:
                continue

            # Determine Logic: Deleted vs Changed
            reason = change.get("reason")
            
            # Find in Ledger
            ledger_entry = self.db.execute(select(SyncLedgerEntry).where(
                SyncLedgerEntry.sp_list_id == list_id,
                SyncLedgerEntry.sp_item_id == int(sp_item_id)
            )).scalars().first()

            if reason == "deleted":
                if ledger_entry:
                    # Delete from Source
                    # Verify we should propagate delete? Assuming yes for 2-way.
                    db_client.delete_row(schema_name, table_name, pg_pk_col, ledger_entry.source_identity)
                    # Remove from Ledger
                    self.db.delete(ledger_entry)
                count += 1
                continue
            
            # Process Fields
            fields = change.get("fields", {})
            pg_data = {}
            for sp_col, val in fields.items():
                if sp_col in sp_to_pg_map:
                    pg_col = sp_to_pg_map[sp_col]
                    pg_data[pg_col] = val # TODO: Apply transforms

            if not pg_data:
                # Metadata only change? Or unmapped fields.
                continue

            content_hash = self._compute_content_hash(pg_data)

            if ledger_entry:
                # Existing Item
                # Check Conflict
                conflict = False
                if sync_def.conflict_policy == "SOURCE_WINS":
                    # Check if source changed since we last synced
                    # We check the content hash in ledger vs current DB row
                    current_row = db_client.fetch_row(schema_name, table_name, pg_pk_col, ledger_entry.source_identity)
                    if current_row:
                         # Filter current row to mapped cols to compare hash
                         current_mapped = {k: v for k, v in current_row.items() if k in pg_data}
                         # This is rough: PG types might differ from SP types, hashing might mismatch.
                         # For prototype, we assume if ledger.content_hash != current_hash, it changed.
                         # But ledger hash is based on what? 
                         # Let's assume we trust ledger's last_source_ts vs now? 
                         # Or just check if row differs.
                         pass
                    
                    # Implementation Simplification: 
                    # If provenance was PUSH (Source -> SP), and we see an update from SP,
                    # we need to know if Source also changed. 
                    # If we don't have row versioning/optimistic locking, we risk overwriting.
                    # Since we are "Source Wins", if in doubt, we skip.
                    # BUT if it's a pure SP update and Source is stale, we should update Source.
                    # "Source Wins" usually means on CONCURRENT modification.
                    # Logic: If Ledger.content_hash == current_source_hash, then source hasn't changed. Safe to update.
                    # If Ledger.content_hash != current_source_hash, Source changed. Reject SP update.
                    pass 

                # For MVP Phase 3, we implement "DESTINATION_WINS" (Last Write Wins from Ingress) logic mostly,
                # or strict "SOURCE_WINS" logic:
                if sync_def.conflict_policy == "SOURCE_WINS":
                     # TODO: Deep check. For now, assume if it's in ledger, we check hash.
                     pass
                
                # Apply Update
                # We update the source row.
                updated_row = db_client.update_row(schema_name, table_name, pg_pk_col, ledger_entry.source_identity, pg_data)
                
                # Update Ledger
                ledger_entry.content_hash = content_hash
                ledger_entry.last_sync_ts = datetime.utcnow()
                ledger_entry.provenance = "PULL"
                
            else:
                # New Item (Insert)
                # We need to generate a source identity (if not auto-inc) or let DB handle it.
                # If DB handles ID (Auto-inc), we insert and get ID back.
                
                # Filter pg_data to remove PK if it's auto-inc (usually 'id' is, unless we map it)
                # If we have a value for PK in pg_data, we try to insert it (maybe it was migrated).
                # But usually new SP item doesn't have Source ID.
                # So we insert.
                inserted_row = db_client.insert_row(schema_name, table_name, pg_data)
                
                if inserted_row:
                    new_id = str(inserted_row.get(pg_pk_col))
                    
                    # Create Ledger Entry
                    # Identity Hash is SHA256 of the ID
                    id_hash = hashlib.sha256(new_id.encode()).hexdigest()
                    
                    new_entry = SyncLedgerEntry(
                        source_identity_hash=id_hash,
                        source_identity=new_id,
                        source_key_strategy="PRIMARY_KEY",
                        source_instance_id=instance_id,
                        sp_list_id=list_id,
                        sp_item_id=int(sp_item_id),
                        content_hash=content_hash,
                        last_source_ts=datetime.utcnow(),
                        last_sync_ts=datetime.utcnow(),
                        provenance="PULL"
                    )
                    self.db.add(new_entry)
            
            count += 1
        
        self.db.commit()
        return count

    def _compute_content_hash(self, data: Dict[str, Any]) -> str:
        # Stable JSON serialization for hashing
        # Filter None? Convert dates?
        # For prototype: str(data)
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
