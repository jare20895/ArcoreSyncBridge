# Arcore SyncBridge Implementation Specifications

This document defines the technical specifications for Arcore SyncBridge, including core data structures, sync behavior, and operational rules.

## 1. Core data structures

### 1.1 DatabaseInstance
```json
{
  "id": "uuid",
  "database_id": "uuid",
  "instance_label": "prod-primary",
  "host": "db01.internal",
  "port": 5432,
  "role": "PRIMARY",
  "priority": 1,
  "status": "ACTIVE"
}
```

### 1.2 SharePointConnection
```json
{
  "id": "uuid",
  "tenant_id": "tenant-id",
  "client_id": "client-id",
  "client_secret": "encrypted-secret",
  "authority_host": "https://login.microsoftonline.com",
  "scopes": ["https://graph.microsoft.com/.default"],
  "status": "ACTIVE"
}
```
Notes:
- client_secret is stored encrypted and is the primary auth source (env vars are optional local-dev overrides).

### 1.3 SyncDefinition
```json
{
  "id": "uuid",
  "name": "Projects Sync",
  "source_table_id": "uuid",
  "target_list_id": "uuid",
  "sync_mode": "ONE_WAY_PUSH",
  "conflict_policy": "SOURCE_WINS",
  "key_strategy": "COMPOSITE_COLUMNS",
  "key_constraint_name": "projects_unique_key",
  "target_strategy": "CONDITIONAL",
  "cursor_strategy": "UPDATED_AT",
  "cursor_column_id": "uuid",
  "sharding_policy": {
    "rules": [
      {"if": "status == 'Active'", "target_list_id": "list-active-id"},
      {"if": "status == 'Closed'", "target_list_id": "list-closed-id"},
      {"if": "age_days >= 365", "target_list_id": "list-archived-id"}
    ],
    "default_target_list_id": "list-active-id"
  }
}
```

### 1.4 SyncSource
```json
{
  "sync_def_id": "uuid",
  "database_instance_id": "uuid",
  "role": "PRIMARY",
  "priority": 1,
  "is_enabled": true
}
```

### 1.5 SyncTarget
```json
{
  "sync_def_id": "uuid",
  "target_list_id": "uuid",
  "is_default": true,
  "priority": 1,
  "status": "ACTIVE"
}
```

### 1.6 SyncKeyColumn
```json
{
  "sync_def_id": "uuid",
  "column_id": "uuid",
  "ordinal_position": 1,
  "is_required": true
}
```

### 1.7 FieldMapping
```json
{
  "source_column_id": "uuid",
  "target_column_id": "uuid",
  "target_type": "number",
  "transform_rule": "CAST_TO_DECIMAL",
  "is_key": false,
  "is_readonly": false
}
```

### 1.8 SyncCursor
```json
{
  "sync_def_id": "uuid",
  "cursor_scope": "SOURCE",
  "cursor_type": "TIMESTAMP",
  "cursor_value": "2025-01-08T12:00:00Z",
  "source_instance_id": "uuid",
  "updated_at": "2025-01-08T12:01:00Z"
}
```

### 1.9 SyncLedgerEntry
```json
{
  "sync_def_id": "uuid",
  "source_identity": "projects|status=Active|code=PRJ-001",
  "source_identity_hash": "sha256",
  "source_key_strategy": "COMPOSITE_COLUMNS",
  "source_instance_id": "uuid",
  "sp_list_id": "guid",
  "sp_item_id": 123,
  "content_hash": "sha256",
  "last_source_ts": "2025-01-08T12:00:00Z",
  "last_sync_ts": "2025-01-08T12:00:30Z",
  "provenance": "PUSH"
}
```

### 1.10 SourceTableMetric
```json
{
  "table_id": "uuid",
  "database_instance_id": "uuid",
  "captured_at": "2025-01-08T12:05:00Z",
  "row_count": 120543,
  "max_updated_at": "2025-01-08T12:04:30Z"
}
```

### 1.11 TargetListMetric
```json
{
  "target_list_id": "uuid",
  "captured_at": "2025-01-08T12:05:10Z",
  "item_count": 120501,
  "last_modified_at": "2025-01-08T12:04:55Z"
}
```

### 1.12 SyncMetrics
```json
{
  "sync_def_id": "uuid",
  "source_instance_id": "uuid",
  "target_list_id": "uuid",
  "last_sync_ts": "2025-01-08T12:05:30Z",
  "total_rows_synced": 980122,
  "last_reconcile_at": "2025-01-08T12:06:00Z",
  "source_row_count": 120543,
  "target_row_count": 120501,
  "reconcile_delta": 42,
  "reconcile_status": "MISMATCH"
}
```

## 2. Metadata extraction workflow
1. Operator selects the parent application and logical database.
2. API connects to the chosen database instance and enumerates schemas and tables.
3. API stores table inventory in database_tables.
4. On table selection, API extracts column names, data types, constraints, and indexes.
5. API stores table_columns, table_constraints, and table_indexes.
6. API creates a schema_snapshot for drift comparison.
7. API records an introspection_run with status and stats.

## 3. Provisioning workflow
1. Operator selects or verifies one or more database instances.
2. API binds selected instances as sync_sources with role and priority.
3. Operator selects a table and reviews columns, constraints, and indexes.
4. Operator selects a SharePoint connection and site.
5. Operator selects one or more SharePoint lists (existing or new).
6. Operator marks a default list and defines conditional routing rules.
7. Operator chooses key strategy (primary key, unique constraint, or composite columns).
8. Operator chooses cursor strategy and watermark column (for UPDATED_AT).
9. API creates missing SharePoint columns and stores mappings in meta-store.
10. API stores canonical SharePoint site/list IDs and selected key strategy.

## 4. Source selection and identity strategy
- Source selection: choose the highest-priority enabled database instance per sync definition.
- Failover: if a primary instance is unavailable, select the next enabled instance by priority.
- Rebind: when a database location changes, create a new database instance and update sync_sources.
- Guardrail: only one PRIMARY source is active for a sync definition to avoid double-writes.
- Row identity: compute source_identity using the selected key strategy.
  - PRIMARY_KEY: use the table primary key column(s).
  - UNIQUE_CONSTRAINT: use the named unique constraint columns.
  - COMPOSITE_COLUMNS: use ordered sync_key_columns.
  - HASHED: hash a normalized JSON of key columns.
- Normalize key values (trim strings, consistent casing, stable type casting) before hashing.
- Store source_identity_hash (SHA-256) in the ledger to prevent duplicates even if row IDs change.
- Scope ledger entries per sync definition; uniqueness is (sync_def_id, source_identity_hash).

## 5. Conditional target routing
- target_strategy SINGLE uses target_list_id directly.
- target_strategy CONDITIONAL evaluates sharding_policy rules in order.
- Rules are evaluated first-match wins; if no match, use default_target_list_id.
- All target_list_id values must exist in sync_targets and be ACTIVE.
- For CONDITIONAL, sharding applies to every push run by default; allow an explicit per-run override to force a single target (backfills/incidents).

## 6. Cursor management
- Push cursors are stored per sync definition and source instance.
- UPDATED_AT uses the cursor_column_id from the sync definition for incremental queries.
- LSN uses database log sequence numbers where supported.
- Pull cursors store Graph delta links per list.
- Cursor updates are written after a successful run to prevent data loss.
- If a source instance changes, the cursor can be reset or re-used depending on key stability.

## 7. Push sync workflow (Postgres -> SharePoint)
1. Worker selects the active database instance for the sync definition.
2. Worker queries rows updated since last cursor value.
3. For each row, compute source_identity and source_identity_hash.
4. Evaluate sharding rules to determine target list (unless a per-run override forces a single target).
5. Fetch ledger entry by source_identity_hash.
6. If no ledger entry, create SharePoint item and insert ledger.
7. If ledger exists and target list matches, hash payload and update if changed.
8. If target list differs, delete item from old list, create item in new list, update ledger.
9. Store source_instance_id on each ledger write for traceability.
10. Advance the source cursor after successful completion.
11. Update sync_metrics with last_sync_ts and total_rows_synced increment.

## 8. Pull sync workflow (SharePoint -> Postgres)
1. Worker calls Graph delta query on each list to fetch changes.
2. For each change, resolve ledger entry by sp_list_id + sp_item_id.
3. Locate source row by source_identity (or composite key columns).
4. Apply updates to Postgres using field mappings.
5. Update ledger hash and provenance to prevent bounce-back.
6. Persist the latest delta link in the target cursor.
7. Update sync_metrics with last_sync_ts and total_rows_synced increment.

## 9. Metrics and reconciliation
- Capture source_table_metrics and target_list_metrics on a scheduled basis or after large runs.
- Reconcile counts per target list when target_strategy is CONDITIONAL.
- Compute reconcile_delta = source_row_count - target_row_count.
- reconcile_status rules:
  - MATCH when delta == 0 or within configured tolerance.
  - MISMATCH when delta exceeds tolerance.
  - UNKNOWN when counts are unavailable.

## 10. Conflict resolution
- SOURCE_WINS: Postgres is authoritative.
- DESTINATION_WINS: SharePoint is authoritative.
- LATEST_WINS: Compare timestamps and apply the newer version.
- MANUAL: Mark conflicts for operator review in the UI.

## 11. Idempotency and safety
- Ledger content hashes prevent redundant updates.
- source_identity_hash is unique per sync definition to avoid duplicates.
- All write operations are retried with exponential backoff.
- Workers use deterministic mapping to avoid duplicate items.

## 12. Rate limiting and batching
- Apply token bucket limits per tenant and per list.
- Batch Graph operations where supported.
- Respect Retry-After headers for 429 and 503 responses.

## 13. Error handling
- Record errors in sync_events with run_id and context.
- Retry transient errors; fail fast on schema or auth errors.
- Provide an operator-visible error summary in the UI.
