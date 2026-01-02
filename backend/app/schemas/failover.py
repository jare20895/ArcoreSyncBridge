from uuid import UUID
from pydantic import BaseModel
from typing import Optional

class FailoverRequest(BaseModel):
    new_primary_instance_id: UUID
    old_primary_instance_id: Optional[UUID] = None # If provided, explicitly marks this as failed/inactive

class FailoverResponse(BaseModel):
    success: bool
    message: str
    updated_source_count: int
