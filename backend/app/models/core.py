import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.db.base import Base

class DatabaseInstance(Base):
    __tablename__ = "database_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_label: Mapped[str] = mapped_column(String, unique=True)
    host: Mapped[str] = mapped_column(String)
    port: Mapped[int] = mapped_column(Integer, default=5432)
    
    db_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Encrypted
    
    role: Mapped[str] = mapped_column(String, default="PRIMARY") # PRIMARY, REPLICA
    priority: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
    
    # Sync sources that use this instance
    sync_sources: Mapped[List["SyncSource"]] = relationship(back_populates="database_instance")


class SharePointConnection(Base):
    __tablename__ = "sharepoint_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String)
    client_id: Mapped[str] = mapped_column(String)
    client_secret: Mapped[Optional[str]] = mapped_column(String, nullable=True) # TODO: Encrypt this
    authority_host: Mapped[str] = mapped_column(String, default="https://login.microsoftonline.com")
    scopes: Mapped[list] = mapped_column(JSONB) # List of scopes
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
    # Encrypted secret would be stored safely, maybe not in this table directly or encrypted


class SyncDefinition(Base):
    __tablename__ = "sync_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    source_table_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True)) # Logical ref to table
    
    # Added to support direct mapping without Inventory tables
    source_schema: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_table_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    target_list_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True) # Default target
    sync_mode: Mapped[str] = mapped_column(String) # ONE_WAY_PUSH, TWO_WAY
    conflict_policy: Mapped[str] = mapped_column(String, default="SOURCE_WINS")
    key_strategy: Mapped[str] = mapped_column(String) # COMPOSITE_COLUMNS, PRIMARY_KEY
    key_constraint_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_strategy: Mapped[str] = mapped_column(String, default="SINGLE") # SINGLE, CONDITIONAL
    cursor_strategy: Mapped[str] = mapped_column(String, default="UPDATED_AT")
    cursor_column_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    sharding_policy: Mapped[dict] = mapped_column(JSONB, default={})
    
    sources: Mapped[List["SyncSource"]] = relationship(back_populates="sync_definition")
    targets: Mapped[List["SyncTarget"]] = relationship(back_populates="sync_definition")
    key_columns: Mapped[List["SyncKeyColumn"]] = relationship(back_populates="sync_definition")
    field_mappings: Mapped[List["FieldMapping"]] = relationship(back_populates="sync_definition")


class SyncSource(Base):
    __tablename__ = "sync_sources"

    sync_def_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sync_definitions.id"), primary_key=True)
    database_instance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("database_instances.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String, default="PRIMARY")
    priority: Mapped[int] = mapped_column(Integer, default=1)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    sync_definition: Mapped["SyncDefinition"] = relationship(back_populates="sources")
    database_instance: Mapped["DatabaseInstance"] = relationship(back_populates="sync_sources")


class SyncTarget(Base):
    __tablename__ = "sync_targets"

    sync_def_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sync_definitions.id"), primary_key=True)
    target_list_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True) # Maps to a SP List (external ID or internal ref)
    
    sharepoint_connection_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sharepoint_connections.id"), nullable=True)
    site_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")

    sync_definition: Mapped["SyncDefinition"] = relationship(back_populates="targets")
    connection: Mapped["SharePointConnection"] = relationship()


class SyncKeyColumn(Base):
    __tablename__ = "sync_key_columns"

    sync_def_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sync_definitions.id"), primary_key=True)
    column_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    ordinal_position: Mapped[int] = mapped_column(Integer)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)

    sync_definition: Mapped["SyncDefinition"] = relationship(back_populates="key_columns")


class FieldMapping(Base):
    __tablename__ = "field_mappings"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_def_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sync_definitions.id"))
    source_column_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    target_column_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    
    # Added to support direct mapping without Inventory tables
    source_column_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_column_name: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Internal Name in SharePoint

    target_type: Mapped[str] = mapped_column(String)
    transform_rule: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_key: Mapped[bool] = mapped_column(Boolean, default=False)
    is_readonly: Mapped[bool] = mapped_column(Boolean, default=False)

    sync_definition: Mapped["SyncDefinition"] = relationship(back_populates="field_mappings")


class SyncCursor(Base):
    __tablename__ = "sync_cursors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_def_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sync_definitions.id"))
    cursor_scope: Mapped[str] = mapped_column(String) # SOURCE, TARGET
    cursor_type: Mapped[str] = mapped_column(String) # TIMESTAMP, LSN, DELTA_TOKEN
    cursor_value: Mapped[str] = mapped_column(String)
    
    source_instance_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    target_list_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SyncLedgerEntry(Base):
    __tablename__ = "sync_ledger"

    sync_def_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    source_identity_hash: Mapped[str] = mapped_column(String, primary_key=True) # SHA256
    source_identity: Mapped[str] = mapped_column(String) # Printable identity
    source_key_strategy: Mapped[str] = mapped_column(String)
    source_instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    
    sp_list_id: Mapped[str] = mapped_column(String) # GUID
    sp_item_id: Mapped[int] = mapped_column(Integer)
    
    content_hash: Mapped[str] = mapped_column(String) # SHA256 of payload
    last_source_ts: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    provenance: Mapped[str] = mapped_column(String) # PUSH, PULL


class MoveAuditLog(Base):
    __tablename__ = "move_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_def_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    source_identity_hash: Mapped[str] = mapped_column(String)
    
    from_list_id: Mapped[str] = mapped_column(String)
    to_list_id: Mapped[str] = mapped_column(String)
    
    moved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String, default="SUCCESS") # SUCCESS, FAILED_ORPHAN
    details: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Error msg or additional info
