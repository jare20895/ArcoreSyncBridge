# CDC (Change Data Capture) Architecture

## Overview
Arcore SyncBridge implements real-time CDC using PostgreSQL logical replication with the `pgoutput` plugin. This provides near real-time synchronization of database changes to SharePoint.

## CDC Architecture Diagram

```mermaid
flowchart TB
    subgraph PG["PostgreSQL Database"]
        WAL[Write-Ahead Log<br/>wal_level=logical]
        Slot[Replication Slot<br/>arcore_sync_slot]
        Plugin[pgoutput Plugin<br/>logical decoding]
        Tables[(Source Tables)]

        Tables -->|INSERT/UPDATE/DELETE| WAL
        WAL --> Slot
        Slot --> Plugin
    end

    subgraph SyncBridge["Arcore SyncBridge"]
        CDCWorker[CDC Worker<br/>psycopg replication]
        Parser[WAL Parser<br/>decode changes]
        Filter[Filter by Table<br/>sync definitions]
        Mapper[Field Mapper<br/>apply mappings]
        Pusher[Push Logic<br/>same as manual sync]

        CDCWorker -->|Stream WAL| Parser
        Parser --> Filter
        Filter --> Mapper
        Mapper --> Pusher
    end

    subgraph MetaStore["Meta-Store"]
        SyncDef[Sync Definitions]
        FieldMaps[Field Mappings]
        Cursors[LSN Cursors]
        Ledger[Sync Ledger]
    end

    subgraph SharePoint["SharePoint"]
        Graph[Microsoft Graph API]
        Lists[SharePoint Lists]

        Graph --> Lists
    end

    Plugin -->|Replicate changes| CDCWorker
    Filter --> SyncDef
    Mapper --> FieldMaps
    Pusher --> Cursors
    Pusher --> Ledger
    Pusher --> Graph

    style PG fill:#e8f5e9
    style SyncBridge fill:#fff3e0
    style MetaStore fill:#e1f5ff
    style SharePoint fill:#fce4ec
```

## CDC Flow - Detailed Sequence

```mermaid
sequenceDiagram
    participant App as Application
    participant PG as PostgreSQL
    participant WAL as Write-Ahead Log
    participant Slot as Replication Slot
    participant CDC as CDC Worker
    participant Parser as WAL Parser
    participant Filter as Table Filter
    participant Pusher as Push Worker
    participant Meta as Meta-Store
    participant Graph as Graph API
    participant SP as SharePoint

    Note over App,PG: 1. Database Change Occurs
    App->>PG: INSERT INTO projects (...)
    PG->>WAL: Write change to WAL
    WAL->>Slot: Store at LSN position

    Note over Slot,CDC: 2. CDC Worker Streams Changes
    CDC->>Slot: SELECT ... FROM pg_logical_slot_get_changes(...)
    Slot-->>CDC: WAL records (LSN, operation, data)

    Note over CDC,Parser: 3. Parse WAL Records
    CDC->>Parser: Raw WAL record
    Parser->>Parser: Decode operation (INSERT/UPDATE/DELETE)
    Parser->>Parser: Extract table name, schema, columns
    Parser-->>CDC: Parsed change event

    Note over CDC,Filter: 4. Filter by Sync Definition
    CDC->>Filter: Change event
    Filter->>Meta: Get sync definitions for table
    Meta-->>Filter: Matching sync_def_id
    Filter-->>CDC: Filtered events

    Note over CDC,Pusher: 5. Apply Field Mappings & Push
    CDC->>Pusher: Trigger push for changed row
    Pusher->>Meta: Get field mappings
    Meta-->>Pusher: Mappings config
    Pusher->>Pusher: Apply type serialization
    Pusher->>Pusher: Evaluate sharding rules
    Pusher->>Meta: Check ledger (INSERT vs UPDATE)
    Meta-->>Pusher: Ledger entry or null
    Pusher->>Graph: Create/Update SharePoint item
    Graph->>SP: Persist to list
    SP-->>Graph: Success
    Graph-->>Pusher: Item created/updated
    Pusher->>Meta: Update ledger (provenance=PUSH)
    Pusher->>Meta: Save LSN cursor checkpoint
    Pusher-->>CDC: Success

    Note over CDC,Slot: 6. Acknowledge & Continue
    CDC->>Slot: Confirm processing (advance confirmed_flush_lsn)
    CDC->>CDC: Loop - wait for next change
```

## CDC Setup Process

```mermaid
flowchart TB
    Start([Start CDC Setup])

    Check1{PostgreSQL<br/>version >= 13?}
    Check2{wal_level =<br/>logical?}
    Check3{Superuser<br/>access?}

    Config1[ALTER SYSTEM SET<br/>wal_level = 'logical']
    Restart[Restart PostgreSQL]
    CreateSlot[CREATE REPLICATION SLOT<br/>via API]
    ConfigSync[Configure Sync Definition<br/>cursor_strategy=LSN]
    StartCDC[Start CDC Worker]
    Monitor[Monitor LSN Lag<br/>& Replication Status]

    End([CDC Active])

    Start --> Check1
    Check1 -->|No| Error1[Upgrade PostgreSQL<br/>to 13+]
    Check1 -->|Yes| Check2
    Check2 -->|No| Check3
    Check2 -->|Yes| CreateSlot
    Check3 -->|No| Error2[Grant superuser<br/>or replication role]
    Check3 -->|Yes| Config1
    Config1 --> Restart
    Restart --> CreateSlot
    CreateSlot --> ConfigSync
    ConfigSync --> StartCDC
    StartCDC --> Monitor
    Monitor --> End

    style Start fill:#e8f5e9
    style End fill:#e8f5e9
    style Error1 fill:#ffebee
    style Error2 fill:#ffebee
    style Monitor fill:#e1f5ff
```

## Replication Slot Management

```mermaid
flowchart LR
    subgraph Operations["Replication Slot Operations"]
        Create[Create Slot<br/>POST /replication/slots]
        List[List Slots<br/>GET /replication/slots/:id]
        Monitor[Monitor Lag<br/>pg_replication_slots]
        Delete[Delete Slot<br/>DELETE /replication/slots]
    end

    subgraph Monitoring["Monitoring Metrics"]
        Lag[LSN Lag<br/>confirmed_flush_lsn vs current]
        Active[Active Status<br/>slot active?]
        Retained[Retained WAL<br/>disk usage]
    end

    subgraph Actions["Maintenance Actions"]
        Pause[Pause CDC Worker<br/>stop consuming]
        Resume[Resume CDC Worker<br/>restart from LSN]
        Reset[Reset Slot<br/>drop & recreate]
    end

    Create --> Monitor
    Monitor --> Monitoring
    Monitoring --> Actions
    Actions --> Delete

    style Operations fill:#e1f5ff
    style Monitoring fill:#fff3e0
    style Actions fill:#ffebee
```

## CDC Worker State Machine

```mermaid
stateDiagram-v2
    [*] --> Initializing
    Initializing --> Connecting: Load config
    Connecting --> Streaming: Establish replication connection
    Streaming --> Processing: Receive WAL record
    Processing --> Streaming: Success
    Processing --> Retrying: Transient error
    Retrying --> Streaming: Retry successful
    Retrying --> Failed: Max retries exceeded
    Failed --> [*]: Stop worker
    Streaming --> Paused: Backpressure threshold
    Paused --> Streaming: Resume signal
    Streaming --> [*]: Shutdown signal

    note right of Initializing
        Load sync definitions
        Get last LSN cursor
    end note

    note right of Processing
        Parse WAL record
        Filter by table
        Apply field mappings
        Push to SharePoint
        Update LSN cursor
    end note

    note right of Paused
        Too many pending changes
        Rate limit exceeded
        Manual pause
    end note
```

## LSN Cursor Management

```mermaid
flowchart TB
    subgraph Init["Initialization"]
        Start([CDC Worker Start])
        LoadCursor[Load Last LSN Cursor<br/>from sync_cursors]
        DefaultLSN{Cursor<br/>exists?}
        CurrentLSN[Get current LSN<br/>pg_current_wal_lsn]
    end

    subgraph Stream["Streaming Loop"]
        GetChanges[pg_logical_slot_get_changes<br/>from LSN cursor]
        ParseWAL[Parse WAL records]
        ProcessChange[Process change event]
        Success{Success?}
    end

    subgraph Checkpoint["Checkpoint"]
        SaveLSN[Save LSN to cursor<br/>sync_cursors.cursor_value]
        ConfirmFlush[Confirm flush to slot<br/>confirmed_flush_lsn]
    end

    Start --> LoadCursor
    LoadCursor --> DefaultLSN
    DefaultLSN -->|No| CurrentLSN
    DefaultLSN -->|Yes| GetChanges
    CurrentLSN --> GetChanges
    GetChanges --> ParseWAL
    ParseWAL --> ProcessChange
    ProcessChange --> Success
    Success -->|Yes| SaveLSN
    Success -->|No| GetChanges
    SaveLSN --> ConfirmFlush
    ConfirmFlush --> GetChanges

    style Init fill:#e8f5e9
    style Stream fill:#fff3e0
    style Checkpoint fill:#e1f5ff
```

## Backpressure & Throttling

```mermaid
flowchart TB
    subgraph Metrics["Monitor Metrics"]
        PendingCount[Pending Changes Count]
        RateLimit[Graph API Rate Limit]
        QueueDepth[Processing Queue Depth]
    end

    subgraph Thresholds["Check Thresholds"]
        Check1{Pending ><br/>1000?}
        Check2{Rate limit<br/>exceeded?}
        Check3{Queue depth<br/>> 500?}
    end

    subgraph Actions["Backpressure Actions"]
        Pause[Pause CDC Stream]
        SlowDown[Reduce Batch Size]
        Wait[Wait for Rate Limit Reset]
        Resume[Resume Normal Operation]
    end

    Metrics --> Thresholds
    PendingCount --> Check1
    RateLimit --> Check2
    QueueDepth --> Check3

    Check1 -->|Yes| Pause
    Check1 -->|No| Check2
    Check2 -->|Yes| Wait
    Check2 -->|No| Check3
    Check3 -->|Yes| SlowDown
    Check3 -->|No| Resume

    Pause --> Resume
    Wait --> Resume
    SlowDown --> Resume

    style Metrics fill:#e1f5ff
    style Thresholds fill:#fff3e0
    style Actions fill:#ffebee
```

## Benefits of CDC over Polling

| Aspect | Polling (UPDATED_AT) | CDC (Logical Replication) |
|--------|---------------------|---------------------------|
| **Latency** | Minutes (batch interval) | Seconds (near real-time) |
| **Database Load** | Repeated full table scans | Stream WAL changes only |
| **Deleted Rows** | Not detected | Captured (DELETE events) |
| **Accuracy** | May miss concurrent updates | Guaranteed all changes |
| **Scalability** | Decreases with table size | Independent of table size |
| **Setup Complexity** | Simple (just add timestamp column) | Moderate (requires superuser, config) |

## Limitations & Considerations

### Performance
- **WAL Retention**: Unprocessed changes consume disk space
- **Replication Lag**: Monitor `confirmed_flush_lsn` vs `sent_lsn`
- **Slot Management**: Inactive slots prevent WAL cleanup

### Operational
- **Superuser Required**: Replication slot creation needs elevated privileges
- **PostgreSQL Restart**: Changing `wal_level` requires restart
- **Slot Cleanup**: Must manually drop slots to reclaim space

### Compatibility
- **PostgreSQL Version**: Requires 13+ for reliable pgoutput
- **AWS RDS**: Supported, use `rds.logical_replication = 1`
- **Azure PostgreSQL**: Supported, set replication support to LOGICAL

## Monitoring Queries

```sql
-- Check replication slot status
SELECT slot_name, active, restart_lsn, confirmed_flush_lsn,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal
FROM pg_replication_slots
WHERE slot_name = 'arcore_sync_slot';

-- Check replication lag
SELECT slot_name,
       pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn) AS lag_bytes
FROM pg_replication_slots
WHERE slot_name = 'arcore_sync_slot';

-- List available WAL files
SELECT * FROM pg_ls_waldir()
ORDER BY modification DESC
LIMIT 10;
```
