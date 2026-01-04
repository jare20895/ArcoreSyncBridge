# One-Way Sync Flow (Push: Database → SharePoint)

## Overview
One-way push sync reads changed rows from PostgreSQL and synchronizes them to SharePoint lists. This is the most common sync mode for use cases where the database is the authoritative source.

## High-Level One-Way Sync Flow

```mermaid
flowchart LR
    Source[(PostgreSQL<br/>Source DB)]
    Worker[Push Worker]
    Ledger[(Sync Ledger<br/>Meta-Store)]
    Graph[Microsoft Graph API]
    Target[SharePoint Lists]

    Source -->|1. SELECT changed rows<br/>WHERE updated_at > cursor| Worker
    Worker -->|2. Check ledger<br/>INSERT vs UPDATE?| Ledger
    Worker -->|3. Apply field mappings<br/>Type serialization| Worker
    Worker -->|4. Create/Update item| Graph
    Graph -->|5. Persist| Target
    Worker -->|6. Update ledger<br/>provenance=PUSH| Ledger
    Worker -->|7. Advance cursor<br/>only on success| Ledger

    style Source fill:#e8f5e9
    style Worker fill:#fff3e0
    style Ledger fill:#e1f5ff
    style Target fill:#fce4ec
```

## Detailed Push Sync Sequence

```mermaid
sequenceDiagram
    participant UI as Web UI
    participant API as API Endpoint
    participant Worker as Push Worker
    participant Meta as Meta-Store
    participant Source as Source DB
    participant Graph as Graph API
    participant SP as SharePoint

    Note over UI,API: User Triggers Sync
    UI->>API: POST /ops/sync/{sync_def_id}

    Note over API,Meta: Create Run Record
    API->>Meta: INSERT INTO sync_runs<br/>(status=RUNNING, run_type=PUSH)
    Meta-->>API: run_id

    Note over API,Worker: Start Push Worker
    API->>Worker: execute_push_sync(sync_def_id)

    Note over Worker,Meta: Load Configuration
    Worker->>Meta: SELECT sync_definition
    Meta-->>Worker: config (mode, strategy, etc.)
    Worker->>Meta: SELECT field_mappings<br/>WHERE sync_direction IN<br/>(BIDIRECTIONAL, PUSH_ONLY)
    Meta-->>Worker: mappings[]
    Worker->>Meta: SELECT sync_cursors<br/>WHERE cursor_scope=SOURCE
    Meta-->>Worker: last_cursor_value

    Note over Worker,Source: Fetch Changed Rows
    Worker->>Source: SELECT * FROM {table}<br/>WHERE {cursor_col} > {cursor_value}<br/>ORDER BY {cursor_col} ASC<br/>LIMIT 1000
    Source-->>Worker: changed_rows[]

    Note over Worker,Graph: Process Each Row
    loop For each row
        Worker->>Worker: Compute source_identity<br/>using key_strategy
        Worker->>Worker: Compute source_identity_hash<br/>SHA-256
        Worker->>Worker: Evaluate sharding_policy<br/>determine target_list

        Note over Worker,Meta: Check Ledger
        Worker->>Meta: SELECT * FROM sync_ledger<br/>WHERE sync_def_id={id}<br/>AND source_identity_hash={hash}
        Meta-->>Worker: ledger_entry or null

        Worker->>Worker: Apply field mappings<br/>Filter by PUSH_ONLY/BIDIRECTIONAL
        Worker->>Worker: Type serialization<br/>datetime→ISO, Decimal→float

        alt Ledger Entry Exists (UPDATE)
            Worker->>Worker: Compute new content_hash
            alt Content changed
                Worker->>Meta: SELECT SharePointList<br/>to resolve GUID
                Meta-->>Worker: sp_list_guid
                Worker->>Graph: PATCH /sites/{site}/lists/{list}/items/{id}<br/>with serialized fields
                Graph->>SP: Update item
                SP-->>Graph: 200 OK
                Graph-->>Worker: Success
                Worker->>Meta: UPDATE sync_ledger<br/>SET content_hash={new_hash},<br/>last_sync_ts=NOW(),<br/>provenance=PUSH
                Worker->>Worker: Advance cursor to row timestamp
            else Content unchanged
                Worker->>Worker: Skip (hash matches)
            end
        else No Ledger Entry (INSERT)
            Worker->>Meta: SELECT SharePointList<br/>to resolve GUID
            Meta-->>Worker: sp_list_guid
            Worker->>Graph: POST /sites/{site}/lists/{list}/items<br/>with serialized fields
            Graph->>SP: Create item
            SP-->>Graph: 201 Created, sp_item_id
            Graph-->>Worker: sp_item_id
            Worker->>Meta: INSERT INTO sync_ledger<br/>VALUES (source_identity_hash,<br/>sp_item_id, content_hash,<br/>provenance=PUSH)
            Worker->>Worker: Advance cursor to row timestamp
        end

        alt Success
            Worker->>Worker: success_count++
        else Error (network, auth, etc.)
            Worker->>Worker: failed_count++<br/>Do NOT advance cursor
            Worker->>Worker: Log error
        end
    end

    Note over Worker,Meta: Save Cursor
    Worker->>Meta: UPDATE sync_cursors<br/>SET cursor_value={max_successful_ts}

    Note over Worker,Meta: Update Run Record
    Worker->>Meta: UPDATE sync_runs<br/>SET status=COMPLETED,<br/>end_time=NOW(),<br/>items_processed={count},<br/>items_failed={failed}
    Worker-->>API: sync_results

    Note over API,UI: Return Results
    API-->>UI: 200 OK<br/>{processed: 120, success: 118, failed: 2}
```

## Push Sync Decision Tree

```mermaid
flowchart TD
    Start([Fetch Changed Row])
    ComputeID[Compute source_identity<br/>using key_strategy]
    HashID[Compute SHA-256<br/>source_identity_hash]
    CheckLedger{Ledger entry<br/>exists?}

    ComputeHash[Compute content_hash<br/>of mapped fields]
    CompareHash{Hash<br/>changed?}

    CheckSharding{Sharding rule<br/>changed?}
    MoveItem[Move Item Logic<br/>DELETE old + CREATE new]
    UpdateItem[Update SharePoint Item<br/>PATCH via Graph API]
    CreateItem[Create SharePoint Item<br/>POST via Graph API]

    UpdateLedger[UPDATE sync_ledger<br/>provenance=PUSH]
    InsertLedger[INSERT sync_ledger<br/>provenance=PUSH]

    AdvanceCursor[Advance Cursor<br/>to row timestamp]
    Success([Success])
    Skip([Skip - unchanged])
    Error([Error - retry next run])

    Start --> ComputeID
    ComputeID --> HashID
    HashID --> CheckLedger

    CheckLedger -->|Yes| ComputeHash
    CheckLedger -->|No| CreateItem

    ComputeHash --> CompareHash
    CompareHash -->|Yes| CheckSharding
    CompareHash -->|No| Skip

    CheckSharding -->|Yes| MoveItem
    CheckSharding -->|No| UpdateItem

    UpdateItem --> UpdateLedger
    MoveItem --> UpdateLedger
    CreateItem --> InsertLedger

    UpdateLedger --> AdvanceCursor
    InsertLedger --> AdvanceCursor
    AdvanceCursor --> Success

    UpdateItem -.->|Graph API Error| Error
    CreateItem -.->|Graph API Error| Error
    MoveItem -.->|Graph API Error| Error

    style Start fill:#e8f5e9
    style Success fill:#c8e6c9
    style Skip fill:#fff9c4
    style Error fill:#ffccbc
```

## Field Mapping & Type Serialization Pipeline

```mermaid
flowchart TB
    subgraph Input["Database Row"]
        R1[id: 123]
        R2[project_code: 'PRJ-001']
        R3[budget_amount: Decimal'450000.00']
        R4[start_date: date'2025-11-06']
        R5[updated_at: datetime'2025-12-21 01:59:16']
        R6[status: 'Active']
    end

    subgraph Mapping["Field Mapping Engine"]
        Load[Load Field Mappings<br/>from sync_definition]
        Filter[Filter by Direction<br/>BIDIRECTIONAL or PUSH_ONLY]
        Map[Apply Column Mapping<br/>source → target]
    end

    subgraph Serialization["Type Serialization"]
        S1[datetime → ISO 8601<br/>'2025-12-21T01:59:16.169893']
        S2[date → datetime → ISO<br/>'2025-11-06T00:00:00']
        S3[Decimal → float<br/>450000.0]
        S4[UUID → string]
        S5[None → null]
    end

    subgraph Output["SharePoint Fields"]
        O1[Title: 'PRJ-001']
        O2[BudgetAmount: 450000.0]
        O3[StartDate: '2025-11-06T00:00:00']
        O4[Status: 'Active']
    end

    Input --> Load
    Load --> Filter
    Filter --> Map
    Map --> Serialization
    Serialization --> Output

    style Input fill:#e8f5e9
    style Mapping fill:#fff3e0
    style Serialization fill:#e1f5ff
    style Output fill:#fce4ec
```

## Cursor Management & Failure Recovery

```mermaid
stateDiagram-v2
    [*] --> LoadCursor: Start sync
    LoadCursor --> FetchRows: cursor_value or null
    FetchRows --> ProcessRow: For each row
    ProcessRow --> CheckSuccess: Push to SharePoint
    CheckSuccess --> AdvanceCursor: Success
    CheckSuccess --> LogError: Failure
    AdvanceCursor --> ProcessRow: Next row
    LogError --> ProcessRow: Continue to next row
    ProcessRow --> SaveCursor: All rows processed
    SaveCursor --> [*]: Sync complete

    note right of LoadCursor
        SELECT cursor_value
        FROM sync_cursors
        WHERE sync_def_id = X
        AND cursor_scope = 'SOURCE'
    end note

    note right of AdvanceCursor
        max_cursor_seen = row.updated_at
        (only if success)
    end note

    note right of SaveCursor
        UPDATE sync_cursors
        SET cursor_value = max_cursor_seen
        (only rows that succeeded)
    end note

    note right of LogError
        Do NOT advance cursor
        Failed row will retry next run
    end note
```

## Sharding Logic - Multi-List Routing

```mermaid
flowchart TB
    Start([Process Row])
    LoadPolicy[Load sharding_policy<br/>from sync_definition]
    CheckStrategy{target_strategy<br/>= CONDITIONAL?}

    UseSingle[Use target_list_id<br/>from definition]
    EvalRules[Evaluate rules<br/>in order]

    Rule1{Rule 1<br/>matches?}
    Rule2{Rule 2<br/>matches?}
    Rule3{Rule 3<br/>matches?}
    DefaultList[Use default_target_list_id]

    ResolveGUID[Resolve SharePoint GUID<br/>from inventory]
    PushToTarget[Push to Target List]

    Start --> LoadPolicy
    LoadPolicy --> CheckStrategy
    CheckStrategy -->|No| UseSingle
    CheckStrategy -->|Yes| EvalRules

    EvalRules --> Rule1
    Rule1 -->|Yes| ResolveGUID
    Rule1 -->|No| Rule2
    Rule2 -->|Yes| ResolveGUID
    Rule2 -->|No| Rule3
    Rule3 -->|Yes| ResolveGUID
    Rule3 -->|No| DefaultList

    UseSingle --> ResolveGUID
    DefaultList --> ResolveGUID
    ResolveGUID --> PushToTarget

    style Start fill:#e8f5e9
    style ResolveGUID fill:#fff3e0
    style PushToTarget fill:#c8e6c9
```

## Example Sharding Configuration

```json
{
  "sync_definition": {
    "id": "uuid",
    "name": "Projects Sync",
    "target_strategy": "CONDITIONAL",
    "sharding_policy": {
      "rules": [
        {
          "if": "status == 'Active'",
          "target_list_id": "active-list-uuid"
        },
        {
          "if": "status == 'Closed'",
          "target_list_id": "closed-list-uuid"
        },
        {
          "if": "budget_amount >= 1000000",
          "target_list_id": "large-projects-uuid"
        }
      ],
      "default_target_list_id": "active-list-uuid"
    }
  }
}
```

## Error Handling & Retry Strategy

```mermaid
flowchart TB
    Start([Graph API Call])
    Success{HTTP<br/>Status?}

    Handle200[200/201 OK<br/>Item created/updated]
    Handle429[429 Too Many Requests<br/>Rate limited]
    Handle503[503 Service Unavailable<br/>Transient error]
    Handle404[404 Not Found<br/>List deleted?]
    Handle401[401 Unauthorized<br/>Auth failed]

    Wait[Wait for Retry-After<br/>or exponential backoff]
    Retry{Retry<br/>count < max?}
    FailItem[Mark item as failed<br/>Do NOT advance cursor]
    FailFatal[Stop sync<br/>Fatal error]

    UpdateLedger[Update Ledger<br/>provenance=PUSH]
    AdvanceCursor[Advance Cursor<br/>to row timestamp]
    Done([Continue])

    Start --> Success
    Success -->|200/201| Handle200
    Success -->|429| Handle429
    Success -->|503| Handle503
    Success -->|404| Handle404
    Success -->|401| Handle401

    Handle200 --> UpdateLedger
    UpdateLedger --> AdvanceCursor
    AdvanceCursor --> Done

    Handle429 --> Wait
    Handle503 --> Wait
    Wait --> Retry
    Retry -->|Yes| Start
    Retry -->|No| FailItem
    FailItem --> Done

    Handle404 --> FailFatal
    Handle401 --> FailFatal

    style Handle200 fill:#c8e6c9
    style FailItem fill:#ffe082
    style FailFatal fill:#ffccbc
```

## Performance Optimization

### Batching Strategy
```mermaid
flowchart LR
    Query[Query changed rows<br/>LIMIT 1000]
    Batch[Process in batches<br/>of 100]
    Parallel[Parallel processing<br/>within rate limits]
    Checkpoint[Checkpoint cursor<br/>every 100 rows]

    Query --> Batch
    Batch --> Parallel
    Parallel --> Checkpoint
    Checkpoint --> Query

    style Query fill:#e8f5e9
    style Batch fill:#fff3e0
    style Parallel fill:#e1f5ff
    style Checkpoint fill:#c8e6c9
```

### Rate Limiting
- **Graph API Limits**: 10,000 requests per 10 minutes per tenant
- **Per-List Limits**: 500 item operations per 10 seconds
- **Mitigation**: Sequential processing per list, respect Retry-After headers

### Cursor Strategy
- **UPDATED_AT**: Use timestamp column for incremental queries
- **LSN**: Use logical sequence number for CDC (see CDC diagram)
- **FULL_SCAN**: No cursor, process all rows each time (not recommended for large tables)

## Monitoring & Observability

```mermaid
flowchart TB
    subgraph Metrics["Sync Metrics"]
        M1[Items Processed]
        M2[Items Failed]
        M3[Duration]
        M4[Cursor Position]
    end

    subgraph Logs["Sync Logs"]
        L1[Run History<br/>sync_runs table]
        L2[Error Messages<br/>per run]
        L3[Ledger Audit Trail<br/>sync_ledger updates]
    end

    subgraph UI["Monitoring UI"]
        U1[Run History Page<br/>Filter by status]
        U2[Sync Definition Detail<br/>Last run stats]
        U3[Drift Reports<br/>Orphaned items]
    end

    Metrics --> Logs
    Logs --> UI

    style Metrics fill:#e1f5ff
    style Logs fill:#fff3e0
    style UI fill:#e8f5e9
```
