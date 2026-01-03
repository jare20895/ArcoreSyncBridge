"""
Database and SharePoint inventory models for metadata tracking.
These models implement the complete DATA_MODEL.md specification.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.db.base import Base


# ============================================================================
# Database Inventory Models
# ============================================================================

class Application(Base):
    """Represents a parent application or product domain."""
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    owner_team: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")  # ACTIVE, ARCHIVED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    databases: Mapped[List["Database"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan"
    )


class Database(Base):
    """
    Represents a logical database (stable identity), decoupled from physical endpoints.
    Multiple database instances can serve the same logical database.
    """
    __tablename__ = "databases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    db_type: Mapped[str] = mapped_column(String, default="POSTGRES")  # POSTGRES, SQLSERVER, MYSQL
    environment: Mapped[str] = mapped_column(String, nullable=False)  # DEV, STAGING, PROD
    database_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")  # ACTIVE, DISABLED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    application: Mapped["Application"] = relationship(back_populates="databases")
    instances: Mapped[List["DatabaseInstance"]] = relationship(
        back_populates="database",
        cascade="all, delete-orphan"
    )
    tables: Mapped[List["DatabaseTable"]] = relationship(
        back_populates="database",
        cascade="all, delete-orphan"
    )


class DatabaseTable(Base):
    """Inventory of tables per database."""
    __tablename__ = "database_tables"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    database_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("databases.id", ondelete="CASCADE"),
        nullable=False
    )
    schema_name: Mapped[str] = mapped_column(String, default="public")
    table_name: Mapped[str] = mapped_column(String, nullable=False)
    table_type: Mapped[str] = mapped_column(String, default="BASE")  # BASE, VIEW
    primary_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    row_estimate: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    last_introspected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    database: Mapped["Database"] = relationship(back_populates="tables")
    columns: Mapped[List["TableColumn"]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan"
    )
    constraints: Mapped[List["TableConstraint"]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan"
    )
    indexes: Mapped[List["TableIndex"]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan"
    )
    metrics: Mapped[List["SourceTableMetric"]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan"
    )
    schema_snapshots: Mapped[List["SchemaSnapshot"]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan"
    )


class TableColumn(Base):
    """Detailed column metadata for a selected table."""
    __tablename__ = "table_columns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("database_tables.id", ondelete="CASCADE"),
        nullable=False
    )
    ordinal_position: Mapped[int] = mapped_column(Integer, nullable=False)
    column_name: Mapped[str] = mapped_column(String, nullable=False)
    data_type: Mapped[str] = mapped_column(String, nullable=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    default_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_identity: Mapped[bool] = mapped_column(Boolean, default=False)
    is_primary_key: Mapped[bool] = mapped_column(Boolean, default=False)
    is_unique: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    table: Mapped["DatabaseTable"] = relationship(back_populates="columns")


class TableConstraint(Base):
    """Constraint definitions for a table."""
    __tablename__ = "table_constraints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("database_tables.id", ondelete="CASCADE"),
        nullable=False
    )
    constraint_name: Mapped[str] = mapped_column(String, nullable=False)
    constraint_type: Mapped[str] = mapped_column(String, nullable=False)  # PRIMARY_KEY, FOREIGN_KEY, UNIQUE, CHECK
    columns: Mapped[list] = mapped_column(JSONB, nullable=False)
    referenced_table: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    table: Mapped["DatabaseTable"] = relationship(back_populates="constraints")


class TableIndex(Base):
    """Index metadata for a table."""
    __tablename__ = "table_indexes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("database_tables.id", ondelete="CASCADE"),
        nullable=False
    )
    index_name: Mapped[str] = mapped_column(String, nullable=False)
    is_unique: Mapped[bool] = mapped_column(Boolean, default=False)
    index_method: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # btree, hash, gin, gist
    columns: Mapped[list] = mapped_column(JSONB, nullable=False)
    definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    table: Mapped["DatabaseTable"] = relationship(back_populates="indexes")


class SourceTableMetric(Base):
    """Source table metrics captured per database instance."""
    __tablename__ = "source_table_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("database_tables.id", ondelete="CASCADE"),
        nullable=False
    )
    database_instance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("database_instances.id", ondelete="CASCADE"),
        nullable=False
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    row_count: Mapped[int] = mapped_column(BigInteger, default=0)
    max_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    table: Mapped["DatabaseTable"] = relationship(back_populates="metrics")
    database_instance: Mapped["DatabaseInstance"] = relationship(back_populates="source_table_metrics")


# ============================================================================
# SharePoint Inventory Models
# ============================================================================

class SharePointSite(Base):
    """Canonical SharePoint site inventory."""
    __tablename__ = "sharepoint_sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sharepoint_connections.id", ondelete="CASCADE"),
        nullable=False
    )
    tenant_id: Mapped[str] = mapped_column(String, nullable=False)
    hostname: Mapped[str] = mapped_column(String, nullable=False)
    site_path: Mapped[str] = mapped_column(String, nullable=False)
    site_id: Mapped[str] = mapped_column(String, nullable=False)
    web_url: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")  # ACTIVE, DISABLED

    # Relationships
    connection: Mapped["SharePointConnection"] = relationship(back_populates="sites")
    lists: Mapped[List["SharePointList"]] = relationship(
        back_populates="site",
        cascade="all, delete-orphan"
    )


class SharePointList(Base):
    """Target lists, either selected or provisioned."""
    __tablename__ = "sharepoint_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sharepoint_sites.id", ondelete="CASCADE"),
        nullable=False
    )
    list_id: Mapped[str] = mapped_column(String, nullable=False)  # SharePoint List GUID
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_provisioned: Mapped[bool] = mapped_column(Boolean, default=False)
    last_provisioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, default="ACTIVE") # ACTIVE, DELETED
    source_table_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("database_tables.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    site: Mapped["SharePointSite"] = relationship(back_populates="lists")
    columns: Mapped[List["SharePointColumn"]] = relationship(
        back_populates="list",
        cascade="all, delete-orphan"
    )
    metrics: Mapped[List["TargetListMetric"]] = relationship(
        back_populates="target_list",
        cascade="all, delete-orphan"
    )


class SharePointColumn(Base):
    """List column metadata for mapping."""
    __tablename__ = "sharepoint_columns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sharepoint_lists.id", ondelete="CASCADE"),
        nullable=False
    )
    column_name: Mapped[str] = mapped_column(String, nullable=False)
    column_type: Mapped[str] = mapped_column(String, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_readonly: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    list: Mapped["SharePointList"] = relationship(back_populates="columns")


class TargetListMetric(Base):
    """SharePoint list metrics captured per list."""
    __tablename__ = "target_list_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_list_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sharepoint_lists.id", ondelete="CASCADE"),
        nullable=False
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    item_count: Mapped[int] = mapped_column(BigInteger, default=0)
    last_modified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    target_list: Mapped["SharePointList"] = relationship(back_populates="metrics")


# ============================================================================
# Monitoring and Metadata Models
# ============================================================================

class IntrospectionRun(Base):
    """Tracks each metadata extraction run per database."""
    __tablename__ = "introspection_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    database_instance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("database_instances.id", ondelete="CASCADE"),
        nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, default="RUNNING")  # RUNNING, SUCCESS, FAILED
    stats: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    database_instance: Mapped["DatabaseInstance"] = relationship(back_populates="introspection_runs")


class SchemaSnapshot(Base):
    """Snapshots of table metadata for drift detection."""
    __tablename__ = "schema_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("database_tables.id", ondelete="CASCADE"),
        nullable=False
    )
    database_instance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("database_instances.id", ondelete="CASCADE"),
        nullable=False
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    columns: Mapped[dict] = mapped_column(JSONB, nullable=False)
    constraints: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    indexes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    table: Mapped["DatabaseTable"] = relationship(back_populates="schema_snapshots")
    database_instance: Mapped["DatabaseInstance"] = relationship(back_populates="schema_snapshots")


class SyncMetric(Base):
    """Rollup metrics per sync definition and target list."""
    __tablename__ = "sync_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_def_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_instance_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    target_list_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_sync_ts: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_rows_synced: Mapped[int] = mapped_column(BigInteger, default=0)
    last_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_reconcile_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_row_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    target_row_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reconcile_delta: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reconcile_status: Mapped[str] = mapped_column(String, default="UNKNOWN")  # MATCH, MISMATCH, UNKNOWN


class SyncEvent(Base):
    """Events logged during sync runs."""
    __tablename__ = "sync_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)  # INFO, WARN, ERROR
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Import statements for relationships (avoid circular imports)
from app.models.core import SharePointConnection, SyncSource  # noqa: E402
