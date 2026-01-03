from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class DatabaseInstanceBase(BaseModel):
    instance_label: str = Field(..., description="Unique label for this database instance")
    host: str = Field(..., description="Hostname or IP address")
    port: int = Field(5432, description="Port number")
    db_name: Optional[str] = Field(None, description="Database Name")
    username: Optional[str] = Field(None, description="Database Username")
    role: str = Field("PRIMARY", description="Role: PRIMARY or REPLICA")
    priority: int = Field(1, description="Priority for failover")
    status: str = Field("ACTIVE", description="Status: ACTIVE, INACTIVE, ERROR")

class DatabaseInstanceCreate(DatabaseInstanceBase):
    password: Optional[str] = Field(None, description="Database Password")

class DatabaseInstanceUpdate(BaseModel):
    instance_label: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    db_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None

class DatabaseInstanceRead(DatabaseInstanceBase):
    id: UUID
    # Password excluded by default

    class Config:
        from_attributes = True

class ConnectionTestRequest(BaseModel):
    host: str
    port: int = 5432
    db_name: str
    username: str
    password: str

class ConnectionTestResult(BaseModel):
    success: bool
    message: str
