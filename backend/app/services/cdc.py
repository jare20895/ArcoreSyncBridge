import time
import logging
import psycopg
import redis
import os
from psycopg.replication import LogicalReplicationConnection
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
        
        # Connect with replication protocol
        try:
            with psycopg.connect(dsn, autocommit=True, row_factory=dict, connection_factory=LogicalReplicationConnection) as conn:
                # 1. Create Slot if not exists (handled by Ops API usually, but auto-create is nice for dev)
                
                # Options for pgoutput: proto_version, publication_names
                # We assume a publication 'arcore_cdc_pub' exists.
                options = {
                    "proto_version": "1",
                    "publication_names": "arcore_cdc_pub"
                }
                
                logger.info(f"Starting replication from LSN {self.start_lsn}")
                
                # Start Replication
                # psycopg 3 'stream' iterator
                gen = conn.stream(
                    self.slot_name,
                    start_lsn=self.start_lsn if self.start_lsn != "0/0" else 0,
                    options=options
                )
                
                for msg in gen:
                    # Check Backpressure
                    while self.redis.xlen(self.stream_key) > self.max_stream_len:
                        logger.warning("Backpressure: Stream full. Pausing ingestion.")
                        time.sleep(1)
                        # TODO: Check if we should stop?

                    # Process Message
                    if msg.payload:
                        self._handle_message(msg)
                    
                    # Persist LSN to DB (Checkpoint)
                    self._checkpoint(msg.wal_end)

        except Exception as e:
            logger.error(f"CDC Worker Failed: {e}")
            raise

    def _handle_message(self, msg):
        # We push the raw payload to Redis. The consumer will decode it.
        # This decouples decoding overhead from the critical ingestion loop.
        # We store LSN with the event.
        
        event_data = {
            "lsn": msg.wal_end,
            "payload": msg.payload, # Bytes
            "instance_id": str(self.instance_id)
        }
        
        self.redis.xadd(self.stream_key, event_data)
        logger.debug(f"Queued WAL message: {len(msg.payload)} bytes")

    def _checkpoint(self, lsn: int):
        # Update DB Instance state
        # Convert int LSN to string "X/Y" for Postgres readability?
        # Psycopg handles LSN as Int/Long often.
        # DB column is String.
        
        # Convert int to PG format X/Y (High 32bit / Low 32bit)
        high = lsn >> 32
        low = lsn & 0xFFFFFFFF
        lsn_str = f"{high:X}/{low:X}"
        
        self.instance.last_wal_lsn = lsn_str
        self.db.commit()
        # logger.debug(f"Checkpointed LSN: {lsn_str}")
