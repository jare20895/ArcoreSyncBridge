from uuid import UUID
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class MoveItemRequest(BaseModel):
    sync_def_id: UUID
    source_identity_hash: str
    target_list_id: UUID
    item_data: Dict[str, Any]

class MoveItemResponse(BaseModel):
    success: bool
    message: str
    new_item_id: Optional[int] = None
