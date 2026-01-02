from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field

# Field Mapping
class FieldMappingBase(BaseModel):
    source_column_id: UUID
    target_column_id: UUID
    source_column_name: Optional[str] = None
    target_column_name: Optional[str] = None
    target_type: str
    transform_rule: Optional[str] = None
    is_key: bool = False
    is_readonly: bool = False

class FieldMappingCreate(FieldMappingBase):
    pass

class FieldMappingRead(FieldMappingBase):
    id: UUID
    sync_def_id: UUID
    class Config:
        from_attributes = True

# Key Column
class SyncKeyColumnBase(BaseModel):
    column_id: UUID
    ordinal_position: int
    is_required: bool = True

class SyncKeyColumnCreate(SyncKeyColumnBase):
    pass

class SyncKeyColumnRead(SyncKeyColumnBase):
    sync_def_id: UUID
    class Config:
        from_attributes = True

# Source
class SyncSourceBase(BaseModel):
    database_instance_id: UUID
    role: str = "PRIMARY"
    priority: int = 1
    is_enabled: bool = True

class SyncSourceCreate(SyncSourceBase):
    pass

class SyncSourceRead(SyncSourceBase):
    sync_def_id: UUID
    class Config:
        from_attributes = True

# Target
class SyncTargetBase(BaseModel):
    target_list_id: UUID
    sharepoint_connection_id: Optional[UUID] = None
    site_id: Optional[str] = None
    is_default: bool = False
    priority: int = 1
    status: str = "ACTIVE"

class SyncTargetCreate(SyncTargetBase):
    pass

class SyncTargetRead(SyncTargetBase):
    sync_def_id: UUID
    class Config:
        from_attributes = True

# Sync Definition
class SyncDefinitionBase(BaseModel):
    name: str
    source_table_id: UUID
    source_schema: Optional[str] = None
    source_table_name: Optional[str] = None
    target_list_id: Optional[UUID] = None
    sync_mode: str = "ONE_WAY_PUSH"
    conflict_policy: str = "SOURCE_WINS"
    key_strategy: str = "PRIMARY_KEY"
    key_constraint_name: Optional[str] = None
    target_strategy: str = "SINGLE"
    cursor_strategy: str = "UPDATED_AT"
    cursor_column_id: Optional[UUID] = None
    sharding_policy: Dict = {}

class SyncDefinitionCreate(SyncDefinitionBase):
    sources: List[SyncSourceCreate] = []
    targets: List[SyncTargetCreate] = []
    key_columns: List[SyncKeyColumnCreate] = []
    field_mappings: List[FieldMappingCreate] = []

class SyncDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    sync_mode: Optional[str] = None
    conflict_policy: Optional[str] = None
    key_strategy: Optional[str] = None
    target_strategy: Optional[str] = None
    cursor_strategy: Optional[str] = None
    sharding_policy: Optional[Dict] = None

class SyncDefinitionRead(SyncDefinitionBase):
    id: UUID
    sources: List[SyncSourceRead]
    targets: List[SyncTargetRead]
    key_columns: List[SyncKeyColumnRead]
    field_mappings: List[FieldMappingRead]

    class Config:
        from_attributes = True
