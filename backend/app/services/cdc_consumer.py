import time
import logging
import redis
import os
import json
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.core import SyncDefinition, SyncSource, SyncLedgerEntry, SyncTarget
from app.services.pgoutput import PgOutputDecoder
from app.services.sharepoint_content import SharePointContentService
from app.services.graph import GraphClient
from app.models.core import SharePointConnection
from app.services.sharding import ShardingEvaluator
import hashlib

logger = logging.getLogger(__name__)

class CDCConsumer:
    def __init__(self, db: Session):
        self.db = db
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.Redis.from_url(self.redis_url)
        self.stream_key = "arcore:cdc:events"
        self.group_name = "arcore_cdc_group"
        self.consumer_name = f"consumer_{os.getpid()}"
        self.decoder = PgOutputDecoder()
        
        # Cache for SyncDefs
        self._sync_def_cache = {} # (instance_id, schema, table) -> SyncDefinition
        self._last_cache_update = 0
        
        self._setup_group()

    def _setup_group(self):
        try:
            self.redis.xgroup_create(self.stream_key, self.group_name, id="0", mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    def run(self):
        logger.info(f"Starting CDC Consumer {self.consumer_name}")
        while True:
            try:
                # Read new messages
                streams = self.redis.xreadgroup(
                    self.group_name, 
                    self.consumer_name, 
                    {self.stream_key: ">"}, 
                    count=10, 
                    block=5000
                )
                
                if not streams:
                    continue
                    
                for stream, messages in streams:
                    for message_id, data in messages:
                        self.process_message(message_id, data)
                        self.redis.xack(self.stream_key, self.group_name, message_id)
                        
            except Exception as e:
                logger.error(f"Consumer Error: {e}")
                time.sleep(1)

    def process_message(self, message_id, data):
        # data is dict of bytes
        payload = data.get(b'payload')
        instance_id_str = data.get(b'instance_id').decode('utf-8')
        
        if not payload:
            return

        decoded = self.decoder.decode(payload)
        if not decoded or decoded["type"] in ("BEGIN", "COMMIT", "RELATION", "UNKNOWN"):
            return

        # INSERT/UPDATE/DELETE
        schema = decoded.get("schema")
        table = decoded.get("table")
        op_type = decoded.get("type")
        row_data = decoded.get("data")
        
        if not schema or not table:
            return

        sync_def = self._get_sync_def(instance_id_str, schema, table)
        if not sync_def:
            # No sync definition for this table
            return
            
        if sync_def.is_paused:
            return

        # Throttle check? 
        # Ideally we check Redis for last processed time for this sync_def.
        
        self._apply_change(sync_def, op_type, row_data)

    def _get_sync_def(self, instance_id: str, schema: str, table: str) -> Optional[SyncDefinition]:
        # Cache refresh every 60s
        if time.time() - self._last_cache_update > 60:
            self._refresh_cache()
            
        return self._sync_def_cache.get((instance_id, schema, table))

    def _refresh_cache(self):
        # Load all active sync definitions with their primary source
        stmt = select(SyncDefinition, SyncSource).join(SyncSource).where(
            SyncDefinition.cdc_enabled == True,
            SyncSource.role == "PRIMARY"
        )
        results = self.db.execute(stmt).all()
        
        self._sync_def_cache = {}
        for sync_def, source in results:
            key = (str(source.database_instance_id), sync_def.source_schema or "public", sync_def.source_table_name)
            self._sync_def_cache[key] = sync_def
        
        self._last_cache_update = time.time()

    def _apply_change(self, sync_def: SyncDefinition, op_type: str, row_data: dict):
        # Resolve Target
        # Sharding support
        target_list_id = None
        if sync_def.target_strategy == "CONDITIONAL":
            evaluator = ShardingEvaluator(sync_def.sharding_policy)
            # row_data from decoder is dict {col: val}.
            # ShardingEvaluator expects dict.
            shard_uuid = evaluator.evaluate(row_data)
            if shard_uuid:
                target_list_id = str(shard_uuid)
        
        if not target_list_id:
            # Default target
            if not sync_def.target_list_id:
                logger.warning(f"No target for SyncDef {sync_def.id}")
                return
            target_list_id = str(sync_def.target_list_id)

        # Resolve Context (Connection/Site)
        # Fetch Target Object to get context
        target = self.db.get(SyncTarget, (sync_def.id, UUID(target_list_id)))
        if not target:
             # Try default?
             # Just use fallback
             target = self.db.execute(select(SyncTarget).where(
                 SyncTarget.sync_def_id == sync_def.id,
                 SyncTarget.is_default == True
             )).scalars().first()
             if not target: 
                 return # Cannot sync
        
        conn_id = target.sharepoint_connection_id
        site_id = target.site_id or os.environ.get("SHAREPOINT_SITE_ID", "")
        
        if conn_id:
            conn = self.db.get(SharePointConnection, conn_id)
        else:
            conn = self.db.query(SharePointConnection).filter(SharePointConnection.status == "ACTIVE").first()
            
        if not conn:
            return

        client_secret = os.environ.get("AZURE_CLIENT_SECRET", "")
        graph = GraphClient(conn.tenant_id, conn.client_id, client_secret, conn.authority_host)
        content_service = SharePointContentService(graph)

        # Map Fields
        sp_data = {}
        pg_pk_col = "id"
        pg_pk_val = None
        
        for fm in sync_def.field_mappings:
            if fm.source_column_name in row_data:
                sp_data[fm.target_column_name] = row_data[fm.source_column_name]
            if fm.is_key and fm.source_column_name:
                pg_pk_col = fm.source_column_name
                
        pg_pk_val = row_data.get(pg_pk_col)
        if not pg_pk_val:
            # Cannot identify row
            return
            
        # Identity Hash
        id_hash = hashlib.sha256(str(pg_pk_val).encode()).hexdigest()
        
        # Ledger Check
        ledger_entry = self.db.get(SyncLedgerEntry, (sync_def.id, id_hash))
        
        if op_type == "DELETE":
            if ledger_entry:
                try:
                    content_service.delete_item(site_id, target_list_id, str(ledger_entry.sp_item_id))
                    self.db.delete(ledger_entry)
                    self.db.commit()
                except Exception as e:
                    logger.error(f"Failed to delete SP item: {e}")
            return

        # INSERT / UPDATE
        # Calculate Hash
        content_hash = hashlib.sha256(json.dumps(sp_data, sort_keys=True, default=str).encode()).hexdigest()
        
        # Loop Prevention: If ledger says this content came from PULL (SharePoint), ignore echo.
        # Wait, if we are in CDC, we are seeing a DB change.
        # If DB change hash matches Ledger hash AND Ledger provenance is PULL, it's an echo.
        
        if ledger_entry and ledger_entry.provenance == "PULL" and ledger_entry.content_hash == content_hash:
            return # Echo

        if ledger_entry:
            # Update
            try:
                content_service.update_item(site_id, target_list_id, str(ledger_entry.sp_item_id), sp_data)
                ledger_entry.content_hash = content_hash
                ledger_entry.provenance = "PUSH"
                ledger_entry.last_sync_ts = datetime.utcnow()
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to update SP item: {e}")
        else:
            # Create
            try:
                sp_id = content_service.create_item(site_id, target_list_id, sp_data)
                new_entry = SyncLedgerEntry(
                    sync_def_id=sync_def.id,
                    source_identity_hash=id_hash,
                    source_identity=str(pg_pk_val),
                    source_key_strategy="PRIMARY_KEY",
                    source_instance_id=UUID(instance_id_str) if instance_id_str else uuid.uuid4(), # Should parse from arg
                    sp_list_id=target_list_id,
                    sp_item_id=int(sp_id),
                    content_hash=content_hash,
                    provenance="PUSH",
                    last_sync_ts=datetime.utcnow()
                )
                self.db.add(new_entry)
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to create SP item: {e}")
