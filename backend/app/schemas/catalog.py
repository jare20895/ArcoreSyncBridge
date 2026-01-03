from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TableInventoryExtractRequest(BaseModel):
    database_id: UUID
    instance_id: UUID
    schema: str = "public"


class TableDetailsExtractRequest(BaseModel):
    instance_id: UUID
    table_ids: List[UUID] = Field(..., min_length=1)


class TableColumnRead(BaseModel):
    id: UUID
    table_id: UUID
    ordinal_position: int
    column_name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str]
    is_identity: bool
    is_primary_key: bool
    is_unique: bool

    class Config:
        from_attributes = True


class TableConstraintRead(BaseModel):
    id: UUID
    table_id: UUID
    constraint_name: str
    constraint_type: str
    columns: List[str]
    referenced_table: Optional[str]
    definition: Optional[str]

    class Config:
        from_attributes = True


class TableIndexRead(BaseModel):
    id: UUID
    table_id: UUID
    index_name: str
    is_unique: bool
    index_method: Optional[str]
    columns: List[str]
    definition: Optional[str]

    class Config:
        from_attributes = True


class DatabaseTableRead(BaseModel):
    id: UUID
    database_id: UUID
    schema_name: str
    table_name: str
    table_type: str
    primary_key: Optional[str]
    row_estimate: Optional[int]
    last_introspected_at: Optional[datetime]
    columns_count: int = 0

    class Config:
        from_attributes = True


class DatabaseTableDetailRead(BaseModel):
    table: DatabaseTableRead
    columns: List[TableColumnRead]
    constraints: List[TableConstraintRead]
    indexes: List[TableIndexRead]


class SharePointSiteResolveRequest(BaseModel):
    connection_id: UUID
    hostname: str
    site_path: str


class SharePointSiteRead(BaseModel):
    id: UUID
    connection_id: UUID
    tenant_id: str
    hostname: str
    site_path: str
    site_id: str
    web_url: str
    status: str

    class Config:
        from_attributes = True


class SharePointListRead(BaseModel):
    id: UUID
    site_id: UUID
    list_id: str
    display_name: str
    description: Optional[str]
    template: Optional[str]
    is_provisioned: bool
    last_provisioned_at: Optional[datetime]
    columns_count: int = 0

    class Config:
        from_attributes = True


class SharePointColumnRead(BaseModel):
    id: UUID
    list_id: UUID
    column_name: str
    column_type: str
    is_required: bool
    is_readonly: bool

    class Config:
        from_attributes = True
