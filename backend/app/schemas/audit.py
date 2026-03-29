from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: UUID
    actor_user_id: Optional[UUID] = None
    actor_email: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    request_id: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
