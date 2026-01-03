from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.core import DatabaseInstance
from app.services.database import DatabaseClient
from app.schemas.replication import ReplicationSlot

class ReplicationService:
    def __init__(self, db: Session):
        self.db = db

    def _get_instance(self, instance_id: UUID) -> DatabaseInstance:
        instance = self.db.get(DatabaseInstance, instance_id)
        if not instance:
            raise ValueError("Database instance not found")
        return instance

    def list_slots(self, instance_id: UUID) -> List[ReplicationSlot]:
        instance = self._get_instance(instance_id)
        client = DatabaseClient(instance)
        
        query = """
            SELECT slot_name, plugin, slot_type, active, restart_lsn, confirmed_flush_lsn 
            FROM pg_replication_slots
        """
        
        try:
            rows = client.execute_raw(query)
            return [
                ReplicationSlot(
                    slot_name=row[0],
                    plugin=row[1],
                    slot_type=row[2],
                    active=row[3],
                    restart_lsn=str(row[4]) if row[4] else None,
                    confirmed_flush_lsn=str(row[5]) if row[5] else None
                ) for row in rows
            ]
        except Exception as e:
            raise RuntimeError(f"Failed to list slots: {e}")

    def create_slot(self, instance_id: UUID, slot_name: str, plugin: str = "pgoutput"):
        instance = self._get_instance(instance_id)
        client = DatabaseClient(instance)
        
        try:
            client.execute_raw("SELECT pg_create_logical_replication_slot(%s, %s)", (slot_name, plugin), autocommit=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create slot: {e}")

    def drop_slot(self, instance_id: UUID, slot_name: str):
        instance = self._get_instance(instance_id)
        client = DatabaseClient(instance)
        
        try:
            client.execute_raw("SELECT pg_drop_replication_slot(%s)", (slot_name,), autocommit=True)
        except Exception as e:
            raise RuntimeError(f"Failed to drop slot: {e}")
