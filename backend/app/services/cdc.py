import time
import logging
import psycopg2
import redis
import os
from psycopg2.extras import LogicalReplicationConnection, ReplicationCursor
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.core import DatabaseInstance, SyncCursor
from app.services.database import DatabaseClient

logger = logging.getLogger(__name__)

class CDCService:
    def __init__(self, db_session: Session, instance_id: UUID):
        self.db = db_session
        self.instance_id = instance_id
        self.instance = self.db.get(DatabaseInstance, instance_id)
        if not self.instance:
            raise ValueError(f"Database instance {instance_id} not found")
        
        # Redis Connection
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.Redis.from_url(self.redis_url)
        self.stream_key = "arcore:cdc:events"
        self.max_stream_len = 10000 # Backpressure limit

        # Use existing client logic to resolve credentials/dsn
        self.client = DatabaseClient(self.instance)
        
        # Determine Slot Name
        self.slot_name = self.instance.replication_slot_name or f"arcore_cdc_{str(self.instance.id).replace('-', '_')}"
        
        # Determine Start LSN from metadata or cursor
        self.start_lsn = self.instance.last_wal_lsn or "0/0"

    def run(self):
        logger.info(f"Starting CDC for instance {self.instance.instance_label} on slot {self.slot_name}")
        
        dsn = self.client.dsn
        # Psycopg2 DSN might be compatible with what DatabaseClient produces (postgresql://...)
        
        try:
            with psycopg2.connect(dsn, connection_factory=LogicalReplicationConnection) as conn:
                cur = conn.cursor()
                
                # Create Slot (if not exists)
                # psycopg2 doesn't have auto-create logic in stream() like v3 might.
                # We need to create it manually if it doesn't exist.
                try:
                    cur.create_replication_slot(self.slot_name, output_plugin='pgoutput')
                except psycopg2.errors.DuplicateObject:
                    pass # Exists
                except Exception as e:
                    logger.warning(f"Slot creation error (might exist): {e}")

                logger.info(f"Starting replication from LSN {self.start_lsn}")
                
                options = {
                    "proto_version": "1",
                    "publication_names": "arcore_cdc_pub"
                }
                
                # Start
                cur.start_replication(
                    slot_name=self.slot_name, 
                    start_lsn=0 if self.start_lsn == "0/0" else int(self.start_lsn.replace('/',''), 16) if '/' in self.start_lsn else 0, # Logic to convert X/Y to int? Wait, psycopg2 expects LSN as int?
                    # No, start_lsn is usually integer (logid * 4G + offset).
                    # '0/0' -> 0.
                    # We need helper to convert.
                    decode=False, # We want raw bytes for pgoutput
                    options=options
                )
                
                def consume_stream(msg):
                    # Check Backpressure
                    while self.redis.xlen(self.stream_key) > self.max_stream_len:
                        logger.warning("Backpressure: Stream full. Pausing ingestion.")
                        time.sleep(1)

                    # Process Message
                    if msg.payload:
                        self._handle_message(msg)
                    
                    # Send Feedback
                    msg.cursor.send_feedback(flush_lsn=msg.data_start)
                    
                    # Persist LSN
                    # msg.data_start is the LSN
                    self._checkpoint(msg.data_start)

                cur.consume_stream(consume_stream)

        except Exception as e:
            logger.error(f"CDC Worker Failed: {e}")
            raise

    def _handle_message(self, msg):
        event_data = {
            "lsn": msg.data_start,
            "payload": msg.payload, # Bytes
            "instance_id": str(self.instance_id)
        }
        
        self.redis.xadd(self.stream_key, event_data)
        logger.debug(f"Queued WAL message: {len(msg.payload)} bytes")

    def _checkpoint(self, lsn: int):
        # Convert int to PG format X/Y (High 32bit / Low 32bit)
        high = lsn >> 32
        low = lsn & 0xFFFFFFFF
        lsn_str = f"{high:X}/{low:X}"
        
        self.instance.last_wal_lsn = lsn_str
        self.db.commit()
