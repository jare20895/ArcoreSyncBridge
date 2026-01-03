import logging
import os
import threading
import time
from typing import Optional
from uuid import UUID

import psycopg2
import redis
from psycopg2.extras import LogicalReplicationConnection
from sqlalchemy.orm import Session

from app.models.core import DatabaseInstance
from app.services.database import DatabaseClient

logger = logging.getLogger(__name__)


class CDCService:
    def __init__(self, db_session: Session, instance_id: UUID, stop_event: Optional[threading.Event] = None):
        self.db = db_session
        self.instance_id = instance_id
        self.instance = self.db.get(DatabaseInstance, instance_id)
        if not self.instance:
            raise ValueError(f"Database instance {instance_id} not found")
        
        self.stop_event = stop_event or threading.Event() # For graceful shutdown

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
        
        try:
            with psycopg2.connect(dsn, connection_factory=LogicalReplicationConnection) as conn:
                cur = conn.cursor()
                
                # Create Slot (if not exists)
                # Assumed to be created by API / Ops endpoint

                logger.info(f"Starting replication from LSN {self.start_lsn}")
                
                options = {
                    "proto_version": "1",
                    "publication_names": "arcore_cdc_pub"
                }
                
                # Start
                cur.start_replication(
                    slot_name=self.slot_name,
                    start_lsn=self._lsn_to_int(self.start_lsn),
                    decode=False,  # We want raw bytes for pgoutput
                    options=options
                )
                
                def consume_stream(msg):
                    if self.stop_event.is_set():
                        raise StopIteration # Graceful exit from consume_stream

                    # Check Backpressure
                    while self.redis.xlen(self.stream_key) > self.max_stream_len:
                        logger.warning("Backpressure: Stream full. Pausing ingestion.")
                        time.sleep(1)
                        if self.stop_event.is_set():
                            raise StopIteration

                    # Process Message
                    if msg.payload:
                        self._handle_message(msg)
                    
                    # Send Feedback
                    msg.cursor.send_feedback(flush_lsn=msg.data_start)
                    
                    # Persist LSN
                    self._checkpoint(msg.data_start)

                cur.consume_stream(consume_stream)

        except StopIteration:
            logger.info("CDC Service stopped gracefully.")
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

    @staticmethod
    def _lsn_to_int(lsn: Optional[str]) -> int:
        if not lsn or lsn == "0/0":
            return 0
        if "/" not in lsn:
            return int(lsn, 16)
        high_str, low_str = lsn.split("/", 1)
        return (int(high_str, 16) << 32) + int(low_str, 16)
