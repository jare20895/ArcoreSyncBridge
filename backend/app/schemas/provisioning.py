from typing import List, Optional, Any
from uuid import UUID
from pydantic import BaseModel
from app.schemas.introspection import ColumnInfo

class ProvisionRequest(BaseModel):
    connection_id: UUID
    hostname: str
    site_path: str
    list_name: str
    description: Optional[str] = ""
    columns: List[ColumnInfo]
    skip_columns: Optional[List[str]] = []

class ProvisionResponse(BaseModel):
    site_id: str
    list: dict
    columns_created: List[dict]
    columns_skipped: List[dict]
    errors: List[dict]
