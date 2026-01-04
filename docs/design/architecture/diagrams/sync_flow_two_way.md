# Two-Way Sync Flow (Bidirectional: Database ↔ SharePoint)

## Overview
Two-way sync provides bidirectional synchronization where changes can originate from either PostgreSQL or SharePoint. The system uses ledger provenance tracking and conflict resolution policies to handle simultaneous changes.

## High-Level Two-Way Sync Flow

```mermaid
flowchart TB
    subgraph Database["PostgreSQL"]
        DBChanges[Changed Rows<br/>updated_at > cursor]
    end

    subgraph SyncBridge["Arcore SyncBridge"]
        PushWorker[Push Worker<br/>DB → SP]
        PullWorker[Pull Worker<br/>SP → DB]
        Ledger[(Sync Ledger<br/>Provenance Tracking)]
        ConflictResolver[Conflict Resolution<br/>Policy Engine]
    end

    subgraph SharePoint["SharePoint"]
        SPChanges[Changed Items<br/>delta query]
    end

    DBChanges -->|1. PUSH| PushWorker
    PushWorker -->|2. Create/Update| SharePoint
    PushWorker -->|3. Update ledger<br/>provenance=PUSH| Ledger

    SPChanges -->|4. PULL| PullWorker
    PullWorker -->|5. Check ledger<br/>conflict?| Ledger
    Ledger -->|6. Conflict detected| ConflictResolver
    ConflictResolver -->|7. Resolve & apply| Database
    PullWorker -->|8. Update ledger<br/>provenance=PULL| Ledger

    style Database fill:#e8f5e9
    style SyncBridge fill:#fff3e0
    style SharePoint fill:#fce4ec
    style Ledger fill:#e1f5ff
    style ConflictResolver fill:#ffecb3
```

## Complete Two-Way Sync Sequence

```mermaid
sequenceDiagram
    participant UI as Web UI
    participant API as API Endpoint
    participant Meta as Meta-Store
    participant Push as Push Worker
    participant Pull as Pull Worker
    participant Source as Source DB
    participant Graph as Graph API
    participant SP as SharePoint

    Note over UI,API: User Triggers Two-Way Sync
    UI->>API: POST /ops/sync/{sync_def_id}<br/>(sync_mode=TWO_WAY)

    Note over API,Push: Phase 1: PUSH (DB → SharePoint)
    API->>Meta: CREATE SyncRun<br/>(run_type=PUSH, status=RUNNING)
    Meta-->>API: push_run_id
    API->>Push: execute_push_sync()

    Push->>Meta: Load field mappings<br/>(BIDIRECTIONAL + PUSH_ONLY)
    Meta-->>Push: mappings[]
    Push->>Meta: Load cursor (SOURCE scope)
    Meta-->>Push: last_timestamp

    Push->>Source: SELECT * WHERE updated_at > cursor
    Source-->>Push: changed_rows[]

    loop For each changed row
        Push->>Push: Apply type serialization
        Push->>Meta: Check ledger
        Meta-->>Push: ledger_entry
        alt Content changed
            Push->>Graph: Create/Update item
            Graph->>SP: Persist
            SP-->>Graph: Success
            Graph-->>Push: sp_item_id
            Push->>Meta: UPDATE ledger<br/>SET provenance=PUSH,<br/>content_hash={hash}
        end
    end

    Push->>Meta: Save cursor (max timestamp)
    Push->>Meta: UPDATE SyncRun<br/>(status=COMPLETED)
    Push-->>API: push_results

    Note over API,Pull: Phase 2: PULL (SharePoint → DB)
    API->>Meta: CREATE SyncRun<br/>(run_type=INGRESS, status=RUNNING)
    Meta-->>API: pull_run_id
    API->>Pull: execute_pull_sync()

    Pull->>Meta: Load field mappings<br/>(BIDIRECTIONAL + PULL_ONLY)
    Meta-->>Pull: mappings[]
    Pull->>Meta: Load cursor (TARGET scope)
    Meta-->>Pull: delta_token

    Pull->>Graph: GET delta query<br/>?deltaToken={token}
    Graph->>SP: Fetch changes
    SP-->>Graph: changed_items[]
    Graph-->>Pull: items[] + new_delta_token

    loop For each changed item
        Pull->>Meta: Find ledger by sp_item_id
        Meta-->>Pull: ledger_entry

        alt Ledger exists
            Pull->>Pull: Compute new content_hash
            Pull->>Pull: Compare with ledger.content_hash

            alt Content changed
                Pull->>Pull: Check ledger.provenance
                alt provenance=PUSH (conflict!)
                    Note over Pull: Both sides changed!
                    Pull->>Pull: Apply conflict_policy<br/>(SOURCE_WINS/DEST_WINS/LATEST_WINS)
                    alt Policy: Apply SharePoint change
                        Pull->>Source: UPDATE row
                        Source-->>Pull: Success
                        Pull->>Meta: UPDATE ledger<br/>SET provenance=PULL
                    else Policy: Keep DB change
                        Pull->>Pull: Skip (DB wins)
                    end
                else provenance=PULL (normal update)
                    Pull->>Source: UPDATE row
                    Source-->>Pull: Success
                    Pull->>Meta: UPDATE ledger<br/>SET provenance=PULL
                end
            end
        else No ledger (new SP item)
            Pull->>Source: INSERT row
            Source-->>Pull: Success
            Pull->>Meta: INSERT ledger<br/>SET provenance=PULL
        end
    end

    Pull->>Meta: Save delta token
    Pull->>Meta: UPDATE SyncRun<br/>(status=COMPLETED)
    Pull-->>API: pull_results

    API-->>UI: Combined results<br/>{push: {...}, ingress: {...}}
```

## Conflict Detection & Resolution

```mermaid
flowchart TB
    Start([Pull finds SharePoint change])
    LoadLedger[Load ledger entry<br/>by sp_item_id]
    LedgerExists{Ledger<br/>exists?}

    ComputeHash[Compute content_hash<br/>of SharePoint item]
    CompareHash{Hash changed<br/>since last sync?}

    CheckProvenance{ledger.provenance<br/>= PUSH?}

    NoConflict[Normal Update<br/>No conflict]
    Conflict[Conflict Detected!<br/>Both sides changed]

    LoadPolicy[Load conflict_policy<br/>from sync_definition]
    ApplyPolicy{Conflict<br/>Policy?}

    SourceWins[SOURCE_WINS<br/>Keep DB change,<br/>skip SharePoint update]
    DestWins[DESTINATION_WINS<br/>Apply SharePoint change<br/>to DB]
    LatestWins[LATEST_WINS<br/>Compare timestamps]
    CompareTS{SharePoint Modified<br/>> DB updated_at?}

    ApplyToDB[UPDATE database row]
    UpdateLedger[UPDATE ledger<br/>provenance=PULL]
    Skip[Skip - DB wins]
    Done([Continue])

    Start --> LoadLedger
    LoadLedger --> LedgerExists

    LedgerExists -->|No| ApplyToDB
    LedgerExists -->|Yes| ComputeHash

    ComputeHash --> CompareHash
    CompareHash -->|No| Skip
    CompareHash -->|Yes| CheckProvenance

    CheckProvenance -->|No (PULL)| NoConflict
    CheckProvenance -->|Yes (PUSH)| Conflict

    NoConflict --> ApplyToDB
    Conflict --> LoadPolicy
    LoadPolicy --> ApplyPolicy

    ApplyPolicy -->|SOURCE_WINS| SourceWins
    ApplyPolicy -->|DESTINATION_WINS| DestWins
    ApplyPolicy -->|LATEST_WINS| LatestWins

    LatestWins --> CompareTS
    CompareTS -->|Yes| DestWins
    CompareTS -->|No| SourceWins

    SourceWins --> Skip
    DestWins --> ApplyToDB

    ApplyToDB --> UpdateLedger
    UpdateLedger --> Done
    Skip --> Done

    style Start fill:#e8f5e9
    style Conflict fill:#ffccbc
    style NoConflict fill:#c8e6c9
    style Done fill:#e8f5e9
```

## Loop Prevention Mechanism

```mermaid
sequenceDiagram
    participant DB as Database
    participant Push as Push Worker
    participant Ledger as Sync Ledger
    participant Graph as Graph API
    participant Pull as Pull Worker

    Note over DB,Push: Scenario: DB row updated
    DB->>Push: Row changed (updated_at incremented)
    Push->>Ledger: Check ledger
    Ledger-->>Push: ledger_entry (provenance=PULL)
    Push->>Push: Compute content_hash
    Push->>Graph: Update SharePoint item
    Graph-->>Push: Success
    Push->>Ledger: UPDATE ledger<br/>SET provenance=PUSH,<br/>content_hash={new}

    Note over Graph,Pull: Pull worker runs (delta query)
    Graph->>Pull: SharePoint item changed
    Pull->>Ledger: Find ledger by sp_item_id
    Ledger-->>Pull: ledger_entry (provenance=PUSH)
    Pull->>Pull: Compute content_hash
    Pull->>Pull: Compare hash

    alt Hash matches (no real change)
        Note over Pull: Loop prevented!<br/>Hash matches, skip update
        Pull->>Pull: Skip - no actual change
    else Hash different (conflict)
        Note over Pull: Real conflict detected
        Pull->>Pull: Apply conflict_policy
    end
```

## Provenance State Machine

```mermaid
stateDiagram-v2
    [*] --> NeverSynced: Item not in ledger

    NeverSynced --> PUSH: Push creates item
    NeverSynced --> PULL: Pull creates item

    PUSH --> PUSH: Push updates item<br/>(hash changed)
    PUSH --> PULL: Pull updates item<br/>(conflict resolved)
    PUSH --> PUSH: Push finds no change<br/>(hash same)
    PUSH --> Conflict: Pull finds change<br/>(hash different)

    PULL --> PULL: Pull updates item<br/>(hash changed)
    PULL --> PUSH: Push updates item<br/>(hash changed)
    PULL --> PULL: Pull finds no change<br/>(hash same)

    Conflict --> PUSH: SOURCE_WINS
    Conflict --> PULL: DESTINATION_WINS
    Conflict --> PUSH: LATEST_WINS (DB newer)
    Conflict --> PULL: LATEST_WINS (SP newer)

    note right of NeverSynced
        First sync creates
        ledger entry with
        provenance direction
    end note

    note right of Conflict
        Both DB and SharePoint
        changed since last sync.
        Apply conflict_policy.
    end note

    note right of PUSH
        Last sync was DB → SharePoint.
        If Pull finds change,
        it's a potential conflict.
    end note

    note right of PULL
        Last sync was SharePoint → DB.
        If Push finds change,
        normal update (no conflict).
    end note
```

## Field Mapping Directional Filtering

```mermaid
flowchart TB
    subgraph Config["Field Mapping Configuration"]
        M1[project_code<br/>BIDIRECTIONAL]
        M2[budget_amount<br/>BIDIRECTIONAL]
        M3[created_by<br/>PULL_ONLY]
        M4[internal_notes<br/>PUSH_ONLY]
        M5[sp_item_id<br/>PULL_ONLY<br/>is_system_field=true]
    end

    subgraph Push["Push Worker (DB → SP)"]
        P1[Filter mappings:<br/>BIDIRECTIONAL + PUSH_ONLY]
        P2[Included:<br/>project_code, budget_amount,<br/>internal_notes]
        P3[Excluded:<br/>created_by, sp_item_id]
    end

    subgraph Pull["Pull Worker (SP → DB)"]
        I1[Filter mappings:<br/>BIDIRECTIONAL + PULL_ONLY]
        I2[Included:<br/>project_code, budget_amount,<br/>created_by, sp_item_id]
        I3[Excluded:<br/>internal_notes]
    end

    Config --> Push
    Config --> Pull

    style Config fill:#e1f5ff
    style Push fill:#e8f5e9
    style Pull fill:#fff3e0
```

## Conflict Resolution Policies

### SOURCE_WINS Policy
```mermaid
flowchart LR
    Conflict[Conflict Detected<br/>Both changed]
    Check[Check Policy]
    Keep[Keep DB Value<br/>Skip SharePoint update]
    Overwrite[Overwrite SharePoint<br/>with DB value on next push]

    Conflict --> Check
    Check --> Keep
    Keep --> Overwrite

    style Conflict fill:#ffccbc
    style Keep fill:#c8e6c9
```

### DESTINATION_WINS Policy
```mermaid
flowchart LR
    Conflict[Conflict Detected<br/>Both changed]
    Check[Check Policy]
    Apply[Apply SharePoint Value<br/>UPDATE database]
    UpdateLedger[Update Ledger<br/>provenance=PULL]

    Conflict --> Check
    Check --> Apply
    Apply --> UpdateLedger

    style Conflict fill:#ffccbc
    style Apply fill:#e1f5ff
    style UpdateLedger fill:#c8e6c9
```

### LATEST_WINS Policy
```mermaid
flowchart TD
    Conflict[Conflict Detected<br/>Both changed]
    Compare{Compare<br/>Timestamps}
    DBNewer[DB updated_at ><br/>SharePoint Modified]
    SPNewer[SharePoint Modified ><br/>DB updated_at]

    KeepDB[Keep DB Value<br/>Skip update]
    ApplySP[Apply SharePoint Value<br/>UPDATE database]

    Conflict --> Compare
    Compare -->|DB newer| DBNewer
    Compare -->|SP newer| SPNewer
    DBNewer --> KeepDB
    SPNewer --> ApplySP

    style Conflict fill:#ffccbc
    style DBNewer fill:#c8e6c9
    style SPNewer fill:#e1f5ff
```

## Delta Query for Pull Sync

```mermaid
sequenceDiagram
    participant Pull as Pull Worker
    participant Meta as Meta-Store
    participant Graph as Graph API
    participant SP as SharePoint

    Note over Pull,Meta: Load Delta Token
    Pull->>Meta: SELECT cursor_value<br/>FROM sync_cursors<br/>WHERE cursor_type=DELTA_LINK
    Meta-->>Pull: delta_token or null

    Note over Pull,Graph: Call Delta Query
    alt First sync (no token)
        Pull->>Graph: GET /sites/{site}/lists/{list}/items<br/>?$expand=fields
        Graph->>SP: Fetch all items
    else Incremental sync (has token)
        Pull->>Graph: GET /sites/{site}/lists/{list}/items/delta<br/>?deltaToken={token}
        Graph->>SP: Fetch changed items
    end

    SP-->>Graph: items[] + @odata.deltaLink
    Graph-->>Pull: Response with new token

    Note over Pull,Meta: Process Changes
    loop For each item
        Pull->>Pull: Process item (see conflict flow)
    end

    Note over Pull,Meta: Save New Token
    Pull->>Meta: UPDATE sync_cursors<br/>SET cursor_value={new_token}
```

## Complete Two-Way Sync State Flow

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> PushRunning: Trigger two-way sync
    PushRunning --> PushProcessing: Load config & cursor

    PushProcessing --> PushFetchRows: Query changed rows
    PushFetchRows --> PushApplyMappings: For each row
    PushApplyMappings --> PushCheckLedger: Type serialization
    PushCheckLedger --> PushCreateUpdate: Resolve INSERT/UPDATE
    PushCreateUpdate --> PushSuccess: Graph API call
    PushSuccess --> PushUpdateLedger: provenance=PUSH
    PushUpdateLedger --> PushAdvanceCursor: Save cursor
    PushAdvanceCursor --> PushFetchRows: Next row
    PushFetchRows --> PushComplete: All rows processed

    PushComplete --> PullRunning: Start pull phase
    PullRunning --> PullProcessing: Load config & delta token

    PullProcessing --> PullFetchChanges: Call delta query
    PullFetchChanges --> PullCheckLedger: For each item
    PullCheckLedger --> PullDetectConflict: Check provenance
    PullDetectConflict --> PullResolve: Apply conflict_policy
    PullResolve --> PullApplyDB: UPDATE/INSERT
    PullApplyDB --> PullUpdateLedger: provenance=PULL
    PullUpdateLedger --> PullSaveToken: Save delta token
    PullSaveToken --> PullFetchChanges: Next item
    PullFetchChanges --> PullComplete: All items processed

    PullComplete --> Idle: Both phases complete

    PushSuccess --> PushFailed: Graph API error
    PushFailed --> PushFetchRows: Continue next row

    PullApplyDB --> PullFailed: DB error
    PullFailed --> PullFetchChanges: Continue next item

    note right of PushUpdateLedger
        Last sync direction = PUSH
        If Pull finds change,
        potential conflict
    end note

    note right of PullUpdateLedger
        Last sync direction = PULL
        If Push finds change,
        normal update
    end note
```

## Example Two-Way Sync Scenario

### Scenario: Concurrent Updates

**Initial State:**
- DB: `budget_amount = 100000`, `updated_at = '2025-01-01 10:00:00'`
- SharePoint: `BudgetAmount = 100000`, `Modified = '2025-01-01 10:00:00'`
- Ledger: `content_hash = 'abc123'`, `provenance = PUSH`

**Step 1: User updates DB**
- DB: `budget_amount = 150000`, `updated_at = '2025-01-02 09:00:00'`

**Step 2: User updates SharePoint (before push sync runs)**
- SharePoint: `BudgetAmount = 200000`, `Modified = '2025-01-02 09:30:00'`

**Step 3: Push sync runs**
- Fetches DB row with budget=150000
- Checks ledger (provenance=PUSH, hash=abc123)
- Computes new hash (def456)
- Updates SharePoint BudgetAmount=150000
- Updates ledger (provenance=PUSH, hash=def456)

**Step 4: Pull sync runs**
- Fetches SharePoint changes via delta (BudgetAmount=150000)
- Wait... Modified timestamp is NEWER than our push!
- **Conflict Detected**: ledger.provenance=PUSH but SharePoint value differs from what we just pushed
- Apply conflict_policy (e.g., LATEST_WINS)
- If LATEST_WINS: Compare timestamps
  - SharePoint Modified (09:30) > DB updated_at (09:00)
  - Apply SharePoint value: UPDATE DB SET budget_amount=200000
  - BUT WAIT: We just pushed 150000 at 09:45!
  - Ledger shows our push was after SharePoint change
  - **No conflict** - hash matches our last push

This demonstrates the importance of content hashing in addition to timestamps.

## Monitoring Two-Way Sync

```mermaid
flowchart TB
    subgraph Metrics["Key Metrics"]
        M1[Push Items Processed]
        M2[Pull Items Processed]
        M3[Conflicts Detected]
        M4[Conflicts Resolved]
        M5[Sync Duration Push vs Pull]
    end

    subgraph Alerts["Alert Conditions"]
        A1[High Conflict Rate<br/>> 10% of items]
        A2[Repeated Conflicts<br/>same item]
        A3[Delta Token Expired<br/>full resync needed]
        A4[Cursor Lag<br/>> 1 hour behind]
    end

    subgraph Reports["Reports"]
        R1[Conflict History<br/>by item]
        R2[Provenance Timeline<br/>PUSH/PULL switches]
        R3[Sync Lag Report<br/>cursor vs current]
    end

    Metrics --> Alerts
    Alerts --> Reports

    style Metrics fill:#e1f5ff
    style Alerts fill:#ffecb3
    style Reports fill:#e8f5e9
```

## Best Practices

### When to Use Two-Way Sync
✅ **Good Use Cases:**
- Collaboration: SharePoint users need to edit data, DB users need to see changes
- Mobile/offline scenarios: SharePoint provides mobile UI
- Approval workflows: SharePoint workflows trigger DB updates

❌ **Avoid When:**
- Database is single source of truth
- SharePoint is read-only reporting
- Complex DB triggers/constraints that would break from SP updates
- High-frequency updates (use CDC + one-way instead)

### Conflict Prevention Strategies
1. **Use PULL_ONLY for SharePoint fields**: Let users edit in SharePoint, never overwrite from DB
2. **Use PUSH_ONLY for calculated fields**: DB-managed fields never change in SharePoint
3. **Schedule push before pull**: Ensures DB changes take precedence
4. **Monitor conflict rate**: High rate indicates users editing both systems

### Field Mapping Recommendations
- **BIDIRECTIONAL**: Core business fields editable in both systems
- **PUSH_ONLY**: Calculated fields, DB-generated IDs, audit timestamps
- **PULL_ONLY**: SharePoint system fields (ID, Created, Modified), user-entered notes
