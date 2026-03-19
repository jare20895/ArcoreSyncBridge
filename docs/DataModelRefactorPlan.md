# Data Model Refactor Plan

## Current Entity Set
- Inventory: `Application`, `Database`, `DatabaseTable`, `TableColumn`, `TableConstraint`, `TableIndex`, `DatabaseInstance`
- SharePoint inventory: `SharePointConnection`, `SharePointSite`, `SharePointList`, `SharePointColumn`
- Sync config: `SyncDefinition`, `SyncSource`, `SyncTarget`, `SyncKeyColumn`, `FieldMapping`
- Operations: `SyncCursor`, `SyncLedgerEntry`, `MoveAuditLog`, `SyncRun`, `ScheduledSyncAudit`, `SyncAlert`, `SyncMetric`, `SyncEvent`

## Current Problems
- Many UUID fields are not enforced as foreign keys.
- Enum-like string columns have no database-level constraints.
- Several critical uniqueness guarantees are not encoded.
- Operational tables are missing indexes for common filters.
- Audit history is incomplete and actor identity is not tracked.
- There is no tenant or organization boundary in the schema.

## Target-State Schema Changes

### Add Constraints
- Unique `(application_id, name)` on `databases`
- Unique `(database_id, schema_name, table_name)` on `database_tables`
- Unique `(table_id, column_name)` on `table_columns`
- Unique `(site_id, list_id)` on `sharepoint_lists`
- Unique `(list_id, column_name)` on `sharepoint_columns`
- Unique `(sync_def_id, source_column_id, target_column_id)` on `field_mappings`

### Add Foreign Keys
- `sync_definitions.source_table_id -> database_tables.id`
- `sync_definitions.target_list_id -> sharepoint_lists.id`
- `sync_runs.sync_def_id -> sync_definitions.id`
- `sync_metrics.sync_def_id -> sync_definitions.id`
- `sync_metrics.source_instance_id -> database_instances.id`
- `sync_metrics.target_list_id -> sharepoint_lists.id`
- `sync_events.sync_run_id -> sync_runs.id`

### Add Auditability
- New `audit_log` table with:
  - actor identifier
  - entity type/id
  - action
  - before/after payloads
  - request/task correlation id
  - timestamp

### Add Governance Support
- New role and membership tables
- Optional `organization_id` on top-level inventory and sync configuration tables
- Approval request table for high-risk actions

## Index Strategy
- `sync_runs(sync_def_id, start_time desc)`
- `sync_runs(status, start_time desc)`
- `sync_ledger(sync_def_id, sp_list_id, sp_item_id)`
- `sync_ledger(sync_def_id, source_identity_hash)`
- `sync_cursors(sync_def_id, cursor_scope, source_instance_id, target_list_id)`
- `field_mappings(sync_def_id)`
- `sync_metrics(sync_def_id, last_reconcile_at desc)`
- `scheduled_sync_audit(sync_def_id, scheduled_time desc)`
- `sync_alerts(is_resolved, severity, created_at desc)`

## Migration Strategy
1. Add nullable FKs, new indexes, and check constraints.
2. Backfill canonical references from existing denormalized values.
3. Dual-read old and new relationship paths where necessary.
4. Shift services to canonical FK-backed logic.
5. Validate data integrity.
6. Tighten nullability and remove obsolete compatibility columns later.

## Risk Notes
- Ledger and cursor compatibility needs careful migration sequencing.
- Backfills should be idempotent and reversible.
- Production rollout should include query plan verification for the new indexes.
