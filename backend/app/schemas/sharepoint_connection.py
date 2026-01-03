from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class SharePointConnectionBase(BaseModel):
    tenant_id: str = Field(..., description="Azure AD Tenant ID")
    client_id: str = Field(..., description="Azure AD Client ID")
    authority_host: str = Field("https://login.microsoftonline.com", description="Authority Host URL")
    hostname: Optional[str] = Field(None, description="SharePoint Hostname (e.g. contoso.sharepoint.com)")
    scopes: List[str] = Field(["https://graph.microsoft.com/.default"], description="OAuth Scopes")
    status: str = Field("ACTIVE", description="Status")

class SharePointConnectionCreate(SharePointConnectionBase):
    client_secret: str = Field(..., description="Client Secret (will be stored)")

class SharePointConnectionUpdate(BaseModel):
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    authority_host: Optional[str] = None
    hostname: Optional[str] = None
    scopes: Optional[List[str]] = None
    status: Optional[str] = None

class SharePointConnectionRead(SharePointConnectionBase):
    id: UUID
    # Exclude client_secret from read

    class Config:
        from_attributes = True
