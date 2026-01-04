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
  "id": "uuid",
  "sync_def_id": "uuid",
  "source_column_id": "uuid",
  "source_column_name": "budget_amount",
  "target_column_id": "uuid",
  "target_column_name": "BudgetAmount",
  "target_type": "number",
  "sync_direction": "BIDIRECTIONAL",
  "is_system_field": false,
  "transform_rule": null,
  "is_key": false
}
```

**Sync Direction Values:**
- `BIDIRECTIONAL`: Field syncs in both push (DB→SP) and pull (SP→DB)
- `PUSH_ONLY`: Field only syncs during push operations (DB→SP)
- `PULL_ONLY`: Field only syncs during pull operations (SP→DB)

**System Fields:**
- When `is_system_field` is `true`, the field is automatically set to `PULL_ONLY`
- System fields are read-only in SharePoint (ID, Created, Modified, etc.)
- Can be mapped to writable database columns for audit tracking

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
1. Create SyncRun record with status=RUNNING, run_type=PUSH
2. Worker selects the active database instance for the sync definition
3. Worker queries rows updated since last cursor value using cursor_column_id
4. For each row:
   a. Compute source_identity and source_identity_hash
   b. Evaluate sharding rules to determine target list (unless per-run override)
   c. Filter field mappings by sync_direction (BIDIRECTIONAL or PUSH_ONLY)
   d. Apply type serialization (datetime→ISO8601, Decimal→float, UUID→string, date→datetime→ISO8601)
   e. Fetch ledger entry by (sync_def_id, source_identity_hash)
   f. Resolve SharePoint list GUID from inventory (not database UUID)
   g. If no ledger entry:
      - Create SharePoint item via Graph API
      - Insert ledger entry with content_hash, provenance=PUSH
      - Increment success_count
      - Advance cursor ONLY on success
   h. If ledger exists and target list matches:
      - Compute new content_hash
      - If hash differs, update SharePoint item
      - Update ledger with new hash, timestamp, provenance=PUSH
      - Increment success_count
      - Advance cursor ONLY on success
   i. If target list differs (sharding rule changed):
      - Delete item from old list
      - Create item in new list
      - Update ledger with new list_id, provenance=PUSH
      - Increment success_count
      - Advance cursor ONLY on success
   j. On any error:
      - Increment failed_count
      - Do NOT advance cursor (allows retry on next run)
5. Save cursor with max successful timestamp
6. Update SyncRun record:
   - status = COMPLETED (if failed_count == 0) or FAILED
   - end_time = now
   - items_processed = success_count + failed_count
   - items_failed = failed_count
   - error_message (if applicable)

**Critical: Cursor advancement only occurs after successful item creation/update. Failed items will be retried on the next sync run.**

## 8. Pull sync workflow (SharePoint -> Postgres)
1. Create SyncRun record with status=RUNNING, run_type=INGRESS
2. Worker fetches cursor with cursor_type=DELTA_LINK for the target list
3. Worker calls Graph delta query to fetch changes since last delta token
4. For each changed item:
   a. Resolve ledger entry by (sync_def_id, sp_list_id, sp_item_id)
   b. Filter field mappings by sync_direction (BIDIRECTIONAL or PULL_ONLY)
   c. Extract SharePoint field values (including system fields if mapped)
   d. If ledger entry exists:
      - Compute new content_hash
      - Check provenance: if last sync was PUSH, apply conflict resolution policy
      - Locate source row by source_identity
      - Apply updates to Postgres using filtered field mappings
      - Update ledger with new hash, timestamp, provenance=PULL
   e. If no ledger entry (item created in SharePoint):
      - Insert new row in Postgres
      - Create ledger entry with provenance=PULL
5. Save new delta token in cursor
6. Update SyncRun record:
   - status = COMPLETED
   - end_time = now
   - items_processed = count of processed items

**Loop Prevention:** Ledger provenance tracks the last sync direction. When provenance=PUSH and a pull finds a change, conflict resolution policy determines whether to apply the change or skip it.

## 9. Metrics and reconciliation
- Capture source_table_metrics and target_list_metrics on a scheduled basis or after large runs.
- Reconcile counts per target list when target_strategy is CONDITIONAL.
- Compute reconcile_delta = source_row_count - target_row_count.
- reconcile_status rules:
  - MATCH when delta == 0 or within configured tolerance.
  - MISMATCH when delta exceeds tolerance.
  - UNKNOWN when counts are unavailable.

## 10. Conflict resolution
When bidirectional sync detects a conflict (both sides modified since last sync):

- **SOURCE_WINS**: Postgres is authoritative, SharePoint changes are overwritten
- **DESTINATION_WINS**: SharePoint is authoritative, Postgres changes are overwritten
- **LATEST_WINS**: Compare last_source_ts vs SharePoint Modified timestamp, apply newer version
- **MANUAL**: Mark conflicts for operator review in the UI (future enhancement)

**Conflict Detection:**
1. Ledger stores `provenance` (PUSH or PULL) and `last_sync_ts`
2. Content hash comparison detects if data changed on either side
3. If both sides changed since last sync → conflict
4. Apply policy to resolve

**Loop Prevention:**
- After push sync, ledger.provenance = PUSH
- If pull sync finds same item unchanged, skip (hash matches)
- If pull sync finds item changed, check provenance:
  - If provenance=PULL, no conflict (just a normal update from SharePoint)
  - If provenance=PUSH, conflict detected (we pushed, but SharePoint was also modified)
- After pull sync, ledger.provenance = PULL

## 11. Idempotency and safety
- Ledger content hashes prevent redundant updates.
- source_identity_hash is unique per sync definition to avoid duplicates.
- All write operations are retried with exponential backoff.
- Workers use deterministic mapping to avoid duplicate items.

## 12. Rate limiting and batching
- Apply token bucket limits per tenant and per list
- Batch Graph operations where supported (batch API endpoints)
- Respect Retry-After headers for 429 (Too Many Requests) and 503 (Service Unavailable)
- Default batch size: 1000 rows per sync run (configurable)
- Parallel worker pools for independent sync definitions
- Backpressure controls for CDC pipelines to prevent overwhelm

**Graph API Limits:**
- Per-app throttling: 10,000 requests per 10 minutes per tenant
- Per-user throttling: 10,000 requests per 10 minutes per user
- Concurrent request limit: 4 concurrent requests per app per tenant
- Item creation/update: 500 requests per 10 seconds per list

**Mitigation:**
- Sequential processing within a single sync definition
- Exponential backoff on 429 responses
- Cursor-based checkpointing allows resume after throttle

## 13. Error handling
- Record errors in SyncRun.error_message for run-level failures
- Record per-item errors in sync_events with run_id and context (future)
- Retry transient errors (429, 503) with exponential backoff
- Fail fast on permanent errors (auth failures, schema mismatches)
- Cursor advancement only on success ensures failed items retry on next run
- Operator-visible error summary in Run History UI (/runs page)

**Error Categories:**
- **Transient**: Network timeout, rate limiting (429), service unavailable (503) → Retry
- **Permanent**: Authentication failure (401), not found (404), schema error → Fail immediately
- **Data**: Type conversion error, constraint violation → Log and skip item

**Cursor Safety:**
When an item fails to sync, the cursor does NOT advance past that item's timestamp. On the next sync run, the failed item will be retried.

## 14. Type serialization for SharePoint API
PostgreSQL types must be serialized to JSON-compatible types before sending to SharePoint Graph API.

**Automatic Type Conversions:**
- `datetime` → ISO 8601 string (e.g., "2025-12-21T01:59:16.169893")
- `date` → datetime at midnight → ISO 8601 string (e.g., "2025-11-06T00:00:00")
- `Decimal` → float (e.g., Decimal('450000.00') → 450000.0)
- `UUID` → string (e.g., UUID('...') → "...")
- `None` → null

**Implementation:**
```python
def _serialize_value_for_sharepoint(self, value: Any) -> Any:
    """Convert Python types to SharePoint/JSON-compatible types."""
    if value is None:
        return None
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, date):
        return datetime.combine(value, datetime.min.time()).isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, UUID):
        return str(value)
    else:
        return value
```

## 15. SharePoint GUID resolution
**Problem:** Database internal UUIDs are not SharePoint list GUIDs.

**Solution:** Always resolve the actual SharePoint GUID from the inventory before making API calls.

```python
# Get SharePoint list record from inventory
sp_list_record = db.get(SharePointList, target_obj.target_list_id)
sp_list_guid = sp_list_record.list_id  # This is the actual SharePoint GUID

# Use the GUID in API calls
content_service.create_item(site_id, sp_list_guid, sp_fields)
content_service.update_item(site_id, sp_list_guid, str(sp_item_id), sp_fields)
```

**Inventory Relationship:**
- `sync_targets.target_list_id` → FK to `sharepoint_lists.id` (database UUID)
- `sharepoint_lists.list_id` → actual SharePoint GUID
- Always use `sharepoint_lists.list_id` for Graph API calls

## 16. Operational features

### 16.1 Reset Cursor
Allows operators to reset sync cursors to force a full resync from the beginning.

**Use Cases:**
- Testing new field mappings
- Recovering from failed sync runs
- Backfilling data after schema changes
- Debugging sync issues

**Implementation:**
- DELETE endpoint: `/api/v1/ops/sync/{sync_def_id}/cursors`
- Deletes all cursors for the sync definition
- Next sync run processes all rows (full scan)
- UI: "Reset Cursor" button in Sync Definition detail page with confirmation dialog

### 16.2 Run History Dashboard
Complete visibility into all sync executions.

**Features:**
- Status filtering (all, completed, failed, running)
- Real-time status updates with animated icons
- Duration calculation and formatting
- Success/failure item counts
- Error message display
- Links to sync definitions
- Run type icons (PUSH, INGRESS, CDC)
- Auto-refresh capability

**Implementation:**
- UI: `/runs` page
- Backend: `/api/v1/runs` endpoint
- Data model: `sync_runs` table

### 16.3 Drift Detection
Identifies orphaned items and count mismatches between source and target.

**Drift Types:**
- **Orphaned Items**: SharePoint items with no matching ledger entry
- **Missing Items**: Source rows with no matching SharePoint item
- **Count Mismatch**: Source row count ≠ target item count

**Implementation:**
- Endpoint: `/api/v1/ops/drift-report`
- Service: `DriftService`
- Report includes: drift type, affected items, recommended actions

### 16.4 Move Logic
Automatically moves items between SharePoint lists when sharding conditions change.

**Workflow:**
1. Detect that sharding rule now routes item to different list
2. Delete item from old list
3. Create item in new list (same fields, new sp_item_id)
4. Update ledger with new sp_list_id and sp_item_id
5. Log move operation in ledger audit trail

**Safety:**
- Transactional: if create fails, move is not recorded
- Audit trail: ledger tracks which list item was moved from/to
- Provenance: maintained across move operations
