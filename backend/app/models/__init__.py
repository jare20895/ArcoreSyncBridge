"""
SQLAlchemy models for Arcore SyncBridge.
Import all models here to ensure they're registered with SQLAlchemy.
"""

# Core sync models
from app.models.core import (
    DatabaseInstance,
    SharePointConnection,
    SyncDefinition,
    SyncSource,
    SyncTarget,
    SyncKeyColumn,
    FieldMapping,
    SyncCursor,
    SyncLedgerEntry,
    MoveAuditLog,
    SyncRun,
)

# Inventory models (full DATA_MODEL spec)
from app.models.inventory import (
    Application,
    Database,
    DatabaseTable,
    TableColumn,
    TableConstraint,
    TableIndex,
    SourceTableMetric,
    SharePointSite,
    SharePointList,
    SharePointColumn,
    TargetListMetric,
    IntrospectionRun,
    SchemaSnapshot,
    SyncMetric,
    SyncEvent,
)

__all__ = [
    # Core
    "DatabaseInstance",
    "SharePointConnection",
    "SyncDefinition",
    "SyncSource",
    "SyncTarget",
    "SyncKeyColumn",
    "FieldMapping",
    "SyncCursor",
    "SyncLedgerEntry",
    "MoveAuditLog",
    "SyncRun",
    # Inventory
    "Application",
    "Database",
    "DatabaseTable",
    "TableColumn",
    "TableConstraint",
    "TableIndex",
    "SourceTableMetric",
    "SharePointSite",
    "SharePointList",
    "SharePointColumn",
    "TargetListMetric",
    "IntrospectionRun",
    "SchemaSnapshot",
    "SyncMetric",
    "SyncEvent",
]
