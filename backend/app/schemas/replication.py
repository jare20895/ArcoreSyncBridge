from typing import Optional
from pydantic import BaseModel

class ReplicationSlot(BaseModel):
    slot_name: str
    plugin: str
    slot_type: str
    active: bool
    restart_lsn: Optional[str] = None
    confirmed_flush_lsn: Optional[str] = None

class CreateSlotRequest(BaseModel):
    instance_id: str # UUID of DatabaseInstance
    slot_name: str
    plugin: str = "pgoutput"

class DropSlotRequest(BaseModel):
    instance_id: str
    slot_name: str
