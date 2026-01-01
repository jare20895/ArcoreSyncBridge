from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class DatabaseInstanceBase(BaseModel):
    instance_label: str = Field(..., description="Unique label for this database instance")
    host: str = Field(..., description="Hostname or IP address")
    port: int = Field(5432, description="Port number")
    role: str = Field("PRIMARY", description="Role: PRIMARY or REPLICA")
    priority: int = Field(1, description="Priority for failover")
    status: str = Field("ACTIVE", description="Status: ACTIVE, INACTIVE, ERROR")

class DatabaseInstanceCreate(DatabaseInstanceBase):
    pass

class DatabaseInstanceUpdate(BaseModel):
    instance_label: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    role: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None

class DatabaseInstanceRead(DatabaseInstanceBase):
    id: UUID

    class Config:
        from_attributes = True

class ConnectionTestResult(BaseModel):
    success: bool
    message: str
