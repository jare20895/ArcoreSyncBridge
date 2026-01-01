from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class SharePointConnectionBase(BaseModel):
    tenant_id: str = Field(..., description="Azure AD Tenant ID")
    client_id: str = Field(..., description="Azure AD Client ID")
    authority_host: str = Field("https://login.microsoftonline.com", description="Authority Host URL")
    scopes: List[str] = Field(["https://graph.microsoft.com/.default"], description="OAuth Scopes")
    status: str = Field("ACTIVE", description="Status")

class SharePointConnectionCreate(SharePointConnectionBase):
    pass

class SharePointConnectionUpdate(BaseModel):
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    authority_host: Optional[str] = None
    scopes: Optional[List[str]] = None
    status: Optional[str] = None

class SharePointConnectionRead(SharePointConnectionBase):
    id: UUID

    class Config:
        from_attributes = True
