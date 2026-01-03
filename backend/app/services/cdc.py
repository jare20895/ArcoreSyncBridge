import time
import logging
import psycopg
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
        
        # Use existing client logic to resolve credentials/dsn
        # We need to inject 'replication=True' into the connection string or connection factory?
        # DatabaseClient stores 'dsn'. We can reuse it but need to pass `replication=True` to connect.
        self.client = DatabaseClient(self.instance)
        
        # Determine Slot Name
        self.slot_name = self.instance.replication_slot_name or f"arcore_cdc_{str(self.instance.id).replace('-', '_')}"
        
        # Determine Start LSN from metadata or cursor
        # We need a Global Cursor for this Instance's Slot?
        # OR we store it on DatabaseInstance (last_wal_lsn)
        self.start_lsn = self.instance.last_wal_lsn or "0/0"

    def run(self):
        logger.info(f"Starting CDC for instance {self.instance.instance_label} on slot {self.slot_name}")
        
        dsn = self.client.dsn
        
        # Connect with replication protocol
        try:
            with psycopg.connect(dsn, autocommit=True, row_factory=dict, connection_factory=LogicalReplicationConnection) as conn:
                # 1. Create Slot if not exists (handled by Ops API usually, but auto-create is nice for dev)
                # Check slot existence?
                # conn.create_replication_slot(self.slot_name, output_plugin='pgoutput') 
                # Better to assume it exists or catch error.
                
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
                    # Process Message
                    if msg.payload:
                        self._handle_message(msg)
                    
                    # Update status periodically or after commit
                    # send_feedback happens automatically in psycopg loop usually if we iterate?
                    # msg.cursor.send_feedback(flush_lsn=msg.wal_end)
                    
                    # Persist LSN to DB (Checkpoint)
                    # Optimization: Don't write to DB every event. Buffer/Batch.
                    # For prototype: Write to instance metadata.
                    
                    self._checkpoint(msg.wal_end)

        except Exception as e:
            logger.error(f"CDC Worker Failed: {e}")
            raise

    def _handle_message(self, msg):
        # msg.payload is bytes (pgoutput format) if using low-level stream?
        # Psycopg 3 might not parse pgoutput body automatically?
        # "The payload is a bytes object... The client is responsible for parsing it."
        
        # Parsing pgoutput in Python is complex.
        # Alternative: Use 'wal2json' plugin? It sends JSON text.
        # Much easier for Python.
        
        # Let's switch ADR/Design to prefer 'wal2json' if available, as it simplifies this step massively.
        # If wal2json is not installed in the postgres image, we are stuck.
        # postgres:15-alpine does NOT include wal2json by default.
        # We would need a custom Dockerfile for DB to install it.
        
        # If we stick to 'pgoutput', we need a parser.
        # There are libraries like `pgoutput`.
        
        # For this prototype, just logging the size.
        logger.debug(f"Received WAL message: {len(msg.payload)} bytes")

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
