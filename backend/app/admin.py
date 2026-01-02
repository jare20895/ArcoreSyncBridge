from sqladmin import ModelView
from app.models.core import (
    DatabaseInstance,
    SharePointConnection,
    SyncDefinition,
    SyncSource,
    SyncTarget,
    FieldMapping,
    SyncLedgerEntry,
    SyncCursor,
    MoveAuditLog
)

class DatabaseInstanceAdmin(ModelView, model=DatabaseInstance):
    column_list = [DatabaseInstance.id, DatabaseInstance.instance_label, DatabaseInstance.host, DatabaseInstance.status]

class SharePointConnectionAdmin(ModelView, model=SharePointConnection):
    column_list = [SharePointConnection.id, SharePointConnection.tenant_id, SharePointConnection.client_id, SharePointConnection.status]

class SyncDefinitionAdmin(ModelView, model=SyncDefinition):
    column_list = [SyncDefinition.id, SyncDefinition.name, SyncDefinition.sync_mode, SyncDefinition.conflict_policy]

class SyncSourceAdmin(ModelView, model=SyncSource):
    column_list = [SyncSource.sync_def_id, SyncSource.database_instance_id, SyncSource.role]

class SyncTargetAdmin(ModelView, model=SyncTarget):
    column_list = [SyncTarget.sync_def_id, SyncTarget.target_list_id, SyncTarget.status]

class FieldMappingAdmin(ModelView, model=FieldMapping):
    column_list = [FieldMapping.id, FieldMapping.sync_def_id, FieldMapping.source_column_name, FieldMapping.target_column_name]

class SyncLedgerEntryAdmin(ModelView, model=SyncLedgerEntry):
    column_list = [SyncLedgerEntry.sync_def_id, SyncLedgerEntry.source_identity, SyncLedgerEntry.sp_item_id, SyncLedgerEntry.provenance, SyncLedgerEntry.last_sync_ts]

class SyncCursorAdmin(ModelView, model=SyncCursor):
    column_list = [SyncCursor.id, SyncCursor.sync_def_id, SyncCursor.cursor_scope, SyncCursor.cursor_value, SyncCursor.updated_at]

class MoveAuditLogAdmin(ModelView, model=MoveAuditLog):
    column_list = [MoveAuditLog.id, MoveAuditLog.from_list_id, MoveAuditLog.to_list_id, MoveAuditLog.status, MoveAuditLog.moved_at]
