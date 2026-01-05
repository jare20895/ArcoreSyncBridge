from typing import Optional, List
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

class PublicationStatus(BaseModel):
    exists: bool
    all_tables: bool
    tables: List[str]

class CreatePublicationRequest(BaseModel):
    instance_id: str
    pub_name: str = "arcore_cdc_pub"
    for_all_tables: bool = True
    tables: List[str] = []

class DropPublicationRequest(BaseModel):
    instance_id: str
    pub_name: str = "arcore_cdc_pub"
