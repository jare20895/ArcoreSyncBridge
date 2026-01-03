from typing import List, Optional
from pydantic import BaseModel

class ColumnInfo(BaseModel):
    name: str
    data_type: str
    is_nullable: bool
    ordinal_position: int
    is_primary_key: bool = False
    default_value: Optional[str] = None
    is_identity: bool = False
    is_unique: bool = False

class TableInfo(BaseModel):
    schema_name: str
    table_name: str
    columns: List[ColumnInfo] = []
    
class SchemaSnapshot(BaseModel):
    instance_id: str
    tables: List[TableInfo]
