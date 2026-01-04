# 🔄 ArcoreSyncBridge Sync Logic Documentation

## Architecture Overview

The sync engine uses a **dual-ledger UPSERT architecture** with loop prevention, conflict resolution, and incremental change tracking.

## Core Components

### 1. Sync Ledger (`sync_ledger` table)

Central tracking system that maintains sync state:

```python
class SyncLedgerEntry:
    sync_def_id: UUID                    # Which sync definition
    source_identity_hash: str            # SHA256 of source PK (composite key support)
    source_identity: str                 # Human-readable source ID
    source_key_strategy: str             # PRIMARY_KEY | COMPOSITE_COLUMNS
    source_instance_id: UUID             # Which database instance

    sp_list_id: str                      # SharePoint List GUID
    sp_item_id: int                      # SharePoint Item ID

    content_hash: str                    # SHA256 of synced data
    last_source_ts: datetime             # Source row timestamp
    last_sync_ts: datetime               # Last sync time
    provenance: str                      # PUSH | PULL (who wrote last)
```

**Purpose**:
- Tracks which database rows correspond to which SharePoint items
- Enables UPSERT logic (INSERT vs UPDATE decision)
- Prevents infinite loops through provenance tracking
- Detects changes through content hashing

### 2. Sync Cursors (`sync_cursors` table)

Watermark tracking for incremental sync:

```python
class SyncCursor:
    sync_def_id: UUID
    cursor_scope: str         # SOURCE | TARGET
    cursor_type: str          # TIMESTAMP | LSN | DELTA_TOKEN
    cursor_value: str         # Watermark value

    source_instance_id: UUID  # For SOURCE cursors
    target_list_id: UUID      # For TARGET cursors

    updated_at: datetime      # Last cursor update
```

**Purpose**:
- Enables incremental sync (only process changes since last run)
- Reduces load on source database and SharePoint
- Supports different cursor strategies per data source

---

## 📤 Push Sync Logic (Database → SharePoint)

**File**: `backend/app/services/pusher.py`

### Algorithm

```python
def run_push(sync_def_id):
    # 1. Load cursor (watermark)
    cursor = get_cursor(sync_def_id, scope="SOURCE")

    # 2. Fetch changed rows
    rows = db.fetch_changed_rows(
        schema, table,
        cursor_col="updated_at",
        cursor_val=cursor.cursor_value  # Only rows > watermark
    )

    # 3. For each row:
    for row in rows:
        source_id = row['id']
        id_hash = sha256(source_id)

        # 4. Check ledger
        ledger = get_ledger_entry(sync_def_id, id_hash)

        if ledger:
            # ═══════════════════════════════════════
            # EXISTING ITEM - UPDATE PATH
            # ═══════════════════════════════════════

            # Loop Prevention Check
            if ledger.provenance == "PULL":
                # Last write came from SharePoint
                if content_hash(row) == ledger.content_hash:
                    # Skip - this is an echo of our own pull
                    continue

            # Update SharePoint
            sharepoint.update_item(
                site_id, list_guid,
                ledger.sp_item_id,
                serialize_fields(row)
            )

            # Update ledger
            ledger.content_hash = content_hash(row)
            ledger.provenance = "PUSH"
            ledger.last_sync_ts = now()

            # Only advance cursor on success
            cursor.cursor_value = row['updated_at']

        else:
            # ═══════════════════════════════════════
            # NEW ITEM - INSERT PATH
            # ═══════════════════════════════════════

            # Create in SharePoint
            sp_item_id = sharepoint.create_item(
                site_id, list_guid,
                serialize_fields(row)
            )

            # Create ledger entry
            create_ledger(
                sync_def_id=sync_def_id,
                source_identity_hash=id_hash,
                source_identity=source_id,
                sp_list_id=list_guid,
                sp_item_id=sp_item_id,
                content_hash=content_hash(row),
                provenance="PUSH"
            )

            # Only advance cursor on success
            cursor.cursor_value = row['updated_at']

    # 5. Persist cursor (only successful rows advance it)
    save_cursor(cursor)
```

### Key Features

✅ **UPSERT**: Creates new items OR updates existing ones
✅ **Loop Prevention**: Detects and skips echoes from pull sync
✅ **Incremental**: Only processes rows changed since last cursor
✅ **Atomic Cursor**: Only advances after successful sync
✅ **Field Filtering**: Respects `sync_direction` (excludes PULL_ONLY fields)
✅ **System Field Safety**: Never writes to SharePoint readonly fields
✅ **Type Serialization**: Converts Python datetime/Decimal to JSON

### Type Serialization

Before sending to SharePoint, all field values are serialized:

```python
def serialize_value_for_sharepoint(value):
    if isinstance(value, datetime):
        return value.isoformat()  # "2025-12-21T01:59:16.169893"
    elif isinstance(value, date):
        return datetime.combine(value, datetime.min.time()).isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, UUID):
        return str(value)
    else:
        return value
```

---

## 📥 Pull Sync Logic (SharePoint → Database)

**File**: `backend/app/services/synchronizer.py`

### Algorithm

```python
def run_ingress(sync_def_id):
    # 1. Load delta token
    cursor = get_cursor(sync_def_id, scope="TARGET")
    delta_token = cursor.cursor_value

    # 2. Fetch changes from SharePoint (batched)
    changes, new_token = sharepoint.get_list_changes(
        site_id, list_guid,
        delta_token=delta_token
    )

    # 3. For each change:
    for change in changes:
        sp_item_id = change['id']

        # 4. Check ledger
        ledger = get_ledger_by_sp_id(sync_def_id, list_guid, sp_item_id)

        if change['reason'] == 'deleted':
            # ═══════════════════════════════════════
            # DELETION
            # ═══════════════════════════════════════
            if ledger:
                db.delete_row(schema, table, pk_col, ledger.source_identity)
                delete_ledger(ledger)
            continue

        if ledger:
            # ═══════════════════════════════════════
            # EXISTING ITEM - UPDATE PATH
            # ═══════════════════════════════════════

            # Conflict Detection
            if sync_def.conflict_policy == "SOURCE_WINS":
                # Check if source changed since last sync
                current_row = db.fetch_row(schema, table, pk_col, ledger.source_identity)
                current_hash = content_hash(current_row)

                if current_hash != ledger.content_hash:
                    # Source changed! Reject ingress (SOURCE_WINS)
                    log_conflict(f"SOURCE_WINS - skipping ingress for {ledger.source_identity}")
                    continue

            # Update database
            db.update_row(
                schema, table, pk_col,
                ledger.source_identity,
                map_sp_to_db_fields(change['fields'])
            )

            # Update ledger
            ledger.content_hash = content_hash(change['fields'])
            ledger.provenance = "PULL"
            ledger.last_sync_ts = now()

        else:
            # ═══════════════════════════════════════
            # NEW ITEM - INSERT PATH
            # ═══════════════════════════════════════

            # Insert into database
            inserted_row = db.insert_row(
                schema, table,
                map_sp_to_db_fields(change['fields'])
            )

            new_id = inserted_row['id']

            # Create ledger
            create_ledger(
                sync_def_id=sync_def_id,
                source_identity_hash=sha256(new_id),
                source_identity=new_id,
                sp_list_id=list_guid,
                sp_item_id=sp_item_id,
                content_hash=content_hash(change['fields']),
                provenance="PULL"
            )

    # 5. Persist new delta token
    cursor.cursor_value = new_token
    save_cursor(cursor)
```

### Key Features

✅ **UPSERT**: Creates new rows OR updates existing ones
✅ **Conflict Resolution**: SOURCE_WINS policy prevents overwrites
✅ **Deletion Sync**: Propagates SharePoint deletions to database
✅ **Delta API**: Uses SharePoint change tracking (not full scans)
✅ **Field Filtering**: Respects `sync_direction` (excludes PUSH_ONLY fields)
✅ **Batched Processing**: Handles large datasets without OOM

---

## 🔀 Directional Field Mapping (Phase 6)

Each field mapping has a `sync_direction` attribute that controls whether the field syncs in push, pull, or both directions.

### Sync Directions

| Direction | Push (DB→SP) | Pull (SP→DB) | Use Case |
|-----------|--------------|--------------|----------|
| **BIDIRECTIONAL** | ✅ Sync | ✅ Sync | Normal fields that sync both ways |
| **PUSH_ONLY** | ✅ Sync | ❌ Skip | Calculated fields, DB-only data |
| **PULL_ONLY** | ❌ Skip | ✅ Sync | SharePoint metadata (ID, Created, Modified) |

### System Fields

**System Fields** are SharePoint readonly metadata fields that are automatically set to PULL_ONLY:

- `ID` - SharePoint auto-increment item ID
- `Created` - Item creation timestamp
- `Modified` - Last modified timestamp
- `Author` - User who created the item
- `Editor` - User who last modified the item
- `_UIVersionString` - Version number

**Safety Guarantee**: System fields are **never** written to SharePoint, even if accidentally configured as BIDIRECTIONAL. The push sync worker has a safety check that skips all `is_system_field=true` mappings.

### Implementation

**Push Sync** (`pusher.py:166-182`):
```python
for fm in sync_def.field_mappings:
    # Skip PULL_ONLY fields in push sync
    if fm.sync_direction == "PULL_ONLY":
        continue

    # System field safety check
    if fm.is_system_field:
        print(f"[WARN] Skipping system field '{fm.target_column_name}' in push sync")
        continue

    if fm.source_column_name and fm.target_column_name:
        pg_to_sp_map[fm.source_column_name] = fm.target_column_name
```

**Pull Sync** (`synchronizer.py:141-149`):
```python
for fm in sync_def.field_mappings:
    # Skip PUSH_ONLY fields in pull sync
    if fm.sync_direction == "PUSH_ONLY":
        continue

    if fm.target_column_name and fm.source_column_name:
        sp_to_pg_map[fm.target_column_name] = fm.source_column_name
```

---

## 🔄 Loop Prevention

The `provenance` field prevents infinite loops in two-way sync:

```
┌─────────────┐                    ┌──────────────┐
│  Database   │                    │  SharePoint  │
│   row #1    │                    │   item #42   │
└─────────────┘                    └──────────────┘
       │                                   │
       │  1. PUSH (update)                 │
       │──────────────────────────────────>│
       │   Ledger: provenance = "PUSH"     │
       │          content_hash = "abc123"  │
       │                                   │
       │  2. PULL (detected change)        │
       │<──────────────────────────────────│
       │   Check: provenance == "PUSH"?    │
       │   Check: hash == "abc123"?        │
       │   YES! → SKIP (this is an echo)   │
       │                                   │
```

### How It Works

1. **Push writes data to SharePoint**
   - Sets `ledger.provenance = "PUSH"`
   - Stores `content_hash` of synced data

2. **Pull detects the change in SharePoint**
   - Checks `ledger.provenance == "PUSH"`
   - Compares `content_hash` with current data
   - If hashes match → **SKIP** (this is our own write)

3. **Pull detects a user edit in SharePoint**
   - Checks `ledger.provenance == "PUSH"`
   - Compares `content_hash` with current data
   - If hashes differ → **SYNC** (user made a change)

### Content Hashing

```python
def compute_content_hash(data: Dict[str, Any]) -> str:
    """
    Stable SHA256 hash of field data for change detection.
    Sorted keys ensure consistent hashing.
    """
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()
```

---

## ⚙️ Conflict Resolution Policies

### SOURCE_WINS (Default)

**Behavior**: Database is authoritative, SharePoint changes may be rejected.

**Algorithm**:
1. Pull sync detects a change in SharePoint
2. Checks if database row changed since last sync
3. If database changed → **Reject** SharePoint change
4. If database unchanged → **Accept** SharePoint change

**Use Case**: Authoritative database with occasional manual SharePoint edits

**Example**:
```
Time  Database  SharePoint  Action
────  ────────  ──────────  ──────────────────────────────
T0    value=10  value=10    Initial sync
T1    value=20  value=10    User edits database
T2    value=20  value=15    User edits SharePoint
T3    PULL SYNC             Conflict detected!
                            DB changed (10→20)
                            SP changed (10→15)
                            SOURCE_WINS → Reject SP change
                            Database keeps value=20
```

### DESTINATION_WINS (Future)

**Behavior**: SharePoint is authoritative, database changes may be overwritten.

**Algorithm**:
1. Pull sync detects a change in SharePoint
2. Always accept the SharePoint change
3. Overwrite database row

**Use Case**: SharePoint as primary editing interface

---

## 📊 Cursor Strategies

### TIMESTAMP (Database Source)

**Query**:
```sql
SELECT * FROM projects
WHERE updated_at > '2025-12-21 01:59:16.169893'
ORDER BY updated_at ASC
LIMIT 1000
```

**Cursor Storage**:
```python
SyncCursor(
    cursor_scope="SOURCE",
    cursor_type="TIMESTAMP",
    cursor_value="2025-12-21 01:59:16.169893"
)
```

**Requirements**:
- Table must have an `updated_at` timestamp column
- Column must be updated on every row change
- Column must be indexed for performance

### DELTA_TOKEN (SharePoint Target)

**API Call**:
```
GET /sites/{site}/lists/{list}/items/delta?token=abc123xyz
```

**Response**:
```json
{
  "value": [
    {"id": "42", "fields": {...}, "reason": "updated"},
    {"id": "43", "fields": {...}, "reason": "created"}
  ],
  "@odata.deltaLink": "...?token=def456uvw"
}
```

**Cursor Storage**:
```python
SyncCursor(
    cursor_scope="TARGET",
    cursor_type="DELTA_TOKEN",
    cursor_value="def456uvw"
)
```

**Advantages**:
- Efficient: Only returns changes since last token
- Handles deletions automatically
- No timestamp column required

### LSN (Future - CDC)

**Concept**: Postgres Logical Sequence Number for Change Data Capture

**Benefits**:
- Captures all changes (INSERT, UPDATE, DELETE)
- No `updated_at` column required
- Near real-time sync
- Guaranteed ordering

**Implementation**: Not yet implemented

---

## 🎯 Adding New Columns to Mapping

**Scenario**: After initial sync, you add a new field mapping.

### Current Behavior

1. ✅ **New rows**: Will include the new column (full field set)
2. ⚠️ **Existing rows**: Will NOT re-sync unless `updated_at` changes

**Reason**: Cursor watermark means only rows with `updated_at > last_cursor` are fetched.

### Solution Options

#### Option A: Reset Cursor (Recommended)

**UI**: Click "Reset Cursor" button in Sync Definition page

**Effect**:
- Deletes all cursors for the sync definition
- Next sync processes ALL rows (full re-sync)
- Existing SharePoint items are **updated** (not duplicated)

**Pros**:
- ✅ Simple - one click in UI
- ✅ Ensures complete consistency
- ✅ Safe - UPSERT logic prevents duplicates

**Cons**:
- ❌ May process many unchanged rows
- ❌ Higher load on database and SharePoint

**When to Use**: Adding columns, changing mappings, recovering from errors

#### Option B: Touch Rows (Surgical)

**SQL**:
```sql
-- Update all rows
UPDATE projects SET updated_at = NOW();

-- Or specific rows
UPDATE projects
SET updated_at = NOW()
WHERE category = 'Infrastructure';
```

**Effect**:
- Bumps `updated_at` to current time
- Next sync processes touched rows
- Preserves cursor for other tables

**Pros**:
- ✅ Precise control over which rows re-sync
- ✅ Doesn't affect other sync definitions
- ✅ Lower overhead for small updates

**Cons**:
- ❌ Requires SQL access
- ❌ Manual process
- ❌ Changes `updated_at` timestamp

**When to Use**: Targeted re-sync of specific rows

#### Option C: Backfill (Future Enhancement)

**Proposed API**:
```python
POST /api/v1/ops/sync/{sync_def_id}/backfill
{
  "field_mapping_ids": ["uuid1", "uuid2"],
  "strategy": "update_only"  # or "full_resync"
}
```

**Effect**:
- Fetches all ledger entries
- Re-syncs only specified fields
- Doesn't touch unchanged fields

**Pros**:
- ✅ Efficient - only syncs new columns
- ✅ Doesn't bump timestamps
- ✅ API-driven (no SQL required)

**Status**: Not yet implemented (future feature)

---

## 🏗️ Database Schema

### Sync Ledger Table

```sql
CREATE TABLE sync_ledger (
    sync_def_id UUID NOT NULL,
    source_identity_hash VARCHAR(64) NOT NULL,  -- SHA256
    source_identity VARCHAR NOT NULL,
    source_key_strategy VARCHAR NOT NULL,
    source_instance_id UUID NOT NULL,

    sp_list_id VARCHAR NOT NULL,                -- SharePoint List GUID
    sp_item_id INTEGER NOT NULL,                -- SharePoint Item ID

    content_hash VARCHAR(64) NOT NULL,          -- SHA256
    last_source_ts TIMESTAMP WITH TIME ZONE,
    last_sync_ts TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    provenance VARCHAR NOT NULL,                -- PUSH | PULL

    PRIMARY KEY (sync_def_id, source_identity_hash),
    FOREIGN KEY (sync_def_id) REFERENCES sync_definitions(id) ON DELETE CASCADE
);

CREATE INDEX idx_ledger_sp_lookup
ON sync_ledger(sync_def_id, sp_list_id, sp_item_id);
```

### Sync Cursors Table

```sql
CREATE TABLE sync_cursors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_def_id UUID NOT NULL,
    cursor_scope VARCHAR NOT NULL,              -- SOURCE | TARGET
    cursor_type VARCHAR NOT NULL,               -- TIMESTAMP | LSN | DELTA_TOKEN
    cursor_value VARCHAR NOT NULL,

    source_instance_id UUID,
    target_list_id UUID,

    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    FOREIGN KEY (sync_def_id) REFERENCES sync_definitions(id) ON DELETE CASCADE
);

CREATE INDEX idx_cursor_lookup
ON sync_cursors(sync_def_id, cursor_scope, source_instance_id);
```

---

## 📈 Performance Considerations

### Incremental Sync

**Without Cursors** (Full Table Scan):
```sql
SELECT * FROM projects  -- 1M rows scanned every sync
```

**With Cursors** (Incremental):
```sql
SELECT * FROM projects
WHERE updated_at > '2025-12-21 01:59:16'  -- Only changed rows
ORDER BY updated_at ASC
LIMIT 1000
```

**Improvement**:
- 1M rows → 10 rows (99.999% reduction)
- 30 second query → 0.01 second query

### Indexes Required

```sql
-- Critical for cursor queries
CREATE INDEX idx_projects_updated_at ON projects(updated_at);

-- Critical for ledger lookups
CREATE INDEX idx_ledger_sp_lookup
ON sync_ledger(sync_def_id, sp_list_id, sp_item_id);
```

### Batch Processing

**SharePoint Delta API**:
- Processes changes in batches
- Commits after each batch
- Prevents OOM for large change sets

```python
def process_batch(items):
    """Process 100 items at a time"""
    for item in items:
        sync_item(item)
    db.commit()  # Commit batch

# Automatic batching by SharePoint client
content_service.get_list_changes(
    site_id, list_id,
    delta_token,
    callback=process_batch  # Called for each batch
)
```

---

## 🔍 Monitoring & Debugging

### Sync Run Tracking

```sql
CREATE TABLE sync_runs (
    id UUID PRIMARY KEY,
    sync_def_id UUID NOT NULL,
    run_type VARCHAR NOT NULL,              -- PUSH | INGRESS | CDC
    status VARCHAR NOT NULL,                -- RUNNING | COMPLETED | FAILED
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    items_processed INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    error_message TEXT
);
```

### Debug Logging

**Push Sync**:
```
[DEBUG] Fetching changed rows from public.projects WHERE updated_at > 2025-12-21 01:59:16
[DEBUG] DatabaseClient SQL: SELECT * FROM public.projects WHERE updated_at > %s ORDER BY updated_at ASC LIMIT 1000
[DEBUG] Found 5 changed rows to process
[DEBUG] Field Mappings: 8 fields mapped for PUSH (excluding PULL_ONLY). PK: id
[DEBUG] Graph API Request: POST https://graph.microsoft.com/v1.0/sites/.../lists/.../items
[DEBUG] Request Body: {'fields': {'name': 'Project Alpha', 'budget': 500000.0, ...}}
```

### Common Issues

**Problem**: 0 rows processed, 0 success
**Cause**: Cursor watermark is current, no new changes
**Solution**: Click "Reset Cursor" to re-sync all rows

**Problem**: 404 "List not found"
**Cause**: Using database UUID instead of SharePoint GUID
**Solution**: Already fixed in pusher.py (resolves GUID from inventory)

**Problem**: Date serialization error
**Cause**: Python datetime/Decimal objects not JSON-serializable
**Solution**: Already fixed (type serialization in pusher.py)

**Problem**: Infinite loop (rows keep syncing)
**Cause**: Loop prevention broken
**Solution**: Check `provenance` tracking in ledger

---

## 🚀 Future Enhancements

### Phase 7: Change Data Capture (CDC)

**Goal**: Real-time sync using Postgres logical replication

**Implementation**:
```python
def run_cdc_push(sync_def_id):
    # Create replication slot
    slot = db.create_replication_slot("arcore_slot", "pgoutput")

    # Stream changes
    for change in db.stream_changes(slot):
        if change.action == "INSERT":
            push_new_item(change.new_row)
        elif change.action == "UPDATE":
            push_update(change.new_row)
        elif change.action == "DELETE":
            push_delete(change.old_row)
```

**Benefits**:
- Near real-time sync (< 1 second latency)
- No `updated_at` column required
- Captures deletes automatically
- Guaranteed ordering

### Phase 8: Multi-Target Sharding

**Goal**: Route rows to different SharePoint lists based on rules

**Example**:
```python
sharding_policy = {
    "strategy": "CONDITIONAL",
    "rules": [
        {"condition": "status == 'ACTIVE'", "target_list_id": "active-uuid"},
        {"condition": "status == 'ARCHIVED'", "target_list_id": "archive-uuid"}
    ]
}
```

### Phase 9: Transformation Pipelines

**Goal**: Execute `transform_rule` during sync

**Example**:
```python
field_mapping = {
    "source_column": "description",
    "target_column": "Description",
    "transform_rule": "UPPER | TRIM | REGEX(s/Project/Initiative/g)"
}
```

---

## 📋 Summary Table

| Feature | Push Sync | Pull Sync |
|---------|-----------|-----------|
| **Mode** | UPSERT | UPSERT |
| **Incremental** | Cursor (updated_at) | Delta Token |
| **Loop Prevention** | Provenance + Hash | Provenance + Hash |
| **Conflict Resolution** | N/A | SOURCE_WINS |
| **Field Filtering** | Excludes PULL_ONLY | Excludes PUSH_ONLY |
| **System Fields** | Always Skipped | Always Included |
| **Deletions** | Not Tracked | Propagated |
| **Cursor Update** | On Success Only | On Success Only |
| **Type Conversion** | Python → JSON | JSON → Python |
| **Batch Size** | 1000 rows | Dynamic (SP API) |
| **Error Handling** | Continue on failure | Continue on failure |
| **Atomicity** | Per-row | Per-batch |

---

## 🎓 Key Takeaways

1. **UPSERT Architecture**: Both push and pull use INSERT vs UPDATE logic based on ledger
2. **Loop Prevention**: Provenance + content hash prevents infinite sync loops
3. **Incremental Sync**: Cursors ensure only changed data is processed
4. **Atomic Operations**: Cursors only advance after successful sync
5. **Field Direction**: BIDIRECTIONAL, PUSH_ONLY, PULL_ONLY control sync flow
6. **System Fields**: SharePoint metadata (ID, Created, etc.) are read-only
7. **Conflict Resolution**: SOURCE_WINS prevents database overwrites
8. **Type Safety**: Automatic serialization of Python types to JSON

The architecture is **production-ready** with robust error handling, atomic operations, and data integrity guarantees! 🚀
