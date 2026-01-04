# Database Schema Visuals

## Complete Meta-Store ER Diagram

```mermaid
erDiagram
    APPLICATION ||--o{ DATABASE : owns
    DATABASE ||--o{ DATABASE_INSTANCE : endpoints
    DATABASE ||--o{ DATABASE_TABLE : inventories
    DATABASE_TABLE ||--o{ TABLE_COLUMN : contains
    DATABASE_TABLE ||--o{ TABLE_CONSTRAINT : enforces
    DATABASE_TABLE ||--o{ TABLE_INDEX : indexes
    DATABASE_TABLE ||--o{ SOURCE_TABLE_METRIC : measures
    DATABASE_INSTANCE ||--o{ SOURCE_TABLE_METRIC : captures

    SHAREPOINT_CONNECTION ||--o{ SHAREPOINT_SITE : connects
    SHAREPOINT_SITE ||--o{ SHAREPOINT_LIST : hosts
    SHAREPOINT_LIST ||--o{ SHAREPOINT_COLUMN : defines
    SHAREPOINT_LIST ||--o{ TARGET_LIST_METRIC : measures

    DATABASE_TABLE ||--o{ SYNC_DEFINITION : sources
    SHAREPOINT_LIST ||--o{ SYNC_DEFINITION : primary_target
    SYNC_DEFINITION ||--o{ SYNC_TARGET : routes
    SHAREPOINT_LIST ||--o{ SYNC_TARGET : allows
    SHAREPOINT_CONNECTION ||--o{ SYNC_TARGET : uses
    SHAREPOINT_SITE ||--o{ SYNC_TARGET : scopes

    SYNC_DEFINITION ||--o{ SYNC_SOURCE : binds
    DATABASE_INSTANCE ||--o{ SYNC_SOURCE : provides

    SYNC_DEFINITION ||--o{ SYNC_KEY_COLUMN : keys
    TABLE_COLUMN ||--o{ SYNC_KEY_COLUMN : identifies

    SYNC_DEFINITION ||--o{ FIELD_MAPPING : maps
    TABLE_COLUMN ||--o{ FIELD_MAPPING : sources
    SHAREPOINT_COLUMN ||--o{ FIELD_MAPPING : targets

    SYNC_DEFINITION ||--o{ SYNC_LEDGER : tracks
    DATABASE_INSTANCE ||--o{ SYNC_LEDGER : sourced_from

    SYNC_DEFINITION ||--o{ SYNC_CURSOR : cursors
    DATABASE_INSTANCE ||--o{ SYNC_CURSOR : source_scope
    SHAREPOINT_LIST ||--o{ SYNC_CURSOR : target_scope

    SYNC_DEFINITION ||--o{ SYNC_RUN : executes
    SYNC_DEFINITION ||--o{ SYNC_METRIC : summarizes

    APPLICATION {
        uuid id PK
        string name
        string owner_team
        string description
        string status
        timestamp created_at
    }

    DATABASE {
        uuid id PK
        uuid application_id FK
        string name
        string db_type
        string environment
        string database_name
        string status
        timestamp created_at
    }

    DATABASE_INSTANCE {
        uuid id PK
        uuid database_id FK
        string instance_label
        string host
        int port
        string db_name
        string db_user
        string db_password
        jsonb config
        string role
        int priority
        string status
        timestamp created_at
    }

    DATABASE_TABLE {
        uuid id PK
        uuid database_id FK
        string schema_name
        string table_name
        string table_type
        string primary_key
        bigint row_estimate
        timestamp last_introspected_at
    }

    TABLE_COLUMN {
        uuid id PK
        uuid table_id FK
        int ordinal_position
        string column_name
        string data_type
        boolean is_nullable
        string default_value
        boolean is_primary_key
    }

    TABLE_CONSTRAINT {
        uuid id PK
        uuid table_id FK
        string constraint_name
        string constraint_type
        jsonb columns
    }

    TABLE_INDEX {
        uuid id PK
        uuid table_id FK
        string index_name
        boolean is_unique
        string index_method
        jsonb columns
    }

    SHAREPOINT_CONNECTION {
        uuid id PK
        string name
        string tenant_id
        string client_id
        string client_secret
        string authority_host
        jsonb scopes
        string status
        timestamp created_at
    }

    SHAREPOINT_SITE {
        uuid id PK
        uuid connection_id FK
        string tenant_id
        string hostname
        string site_path
        string site_id
        string web_url
        string status
    }

    SHAREPOINT_LIST {
        uuid id PK
        uuid site_id FK
        string list_id
        string display_name
        string description
        string template
        boolean is_provisioned
        timestamp last_provisioned_at
    }

    SHAREPOINT_COLUMN {
        uuid id PK
        uuid list_id FK
        string column_name
        string column_type
        boolean is_required
        boolean is_readonly
    }

    SYNC_DEFINITION {
        uuid id PK
        string name
        uuid source_table_id FK
        uuid target_list_id FK
        string sync_mode
        string conflict_policy
        string key_strategy
        string target_strategy
        string cursor_strategy
        uuid cursor_column_id FK
        jsonb sharding_policy
        boolean is_enabled
    }

    SYNC_TARGET {
        uuid id PK
        uuid sync_def_id FK
        uuid target_list_id FK
        uuid connection_id FK
        uuid site_id FK
        boolean is_default
        int priority
        string status
    }

    SYNC_SOURCE {
        uuid id PK
        uuid sync_def_id FK
        uuid database_instance_id FK
        string role
        int priority
        boolean is_enabled
    }

    SYNC_KEY_COLUMN {
        uuid id PK
        uuid sync_def_id FK
        uuid column_id FK
        int ordinal_position
        boolean is_required
    }

    FIELD_MAPPING {
        uuid id PK
        uuid sync_def_id FK
        uuid source_column_id FK
        string source_column_name
        uuid target_column_id FK
        string target_column_name
        string target_type
        string sync_direction
        boolean is_system_field
        string transform_rule
        boolean is_key
    }

    SYNC_LEDGER {
        uuid id PK
        uuid sync_def_id FK
        string source_identity
        string source_identity_hash
        string source_key_strategy
        uuid source_instance_id FK
        string sp_list_id
        int sp_item_id
        string content_hash
        timestamp last_source_ts
        timestamp last_sync_ts
        string provenance
    }

    SYNC_CURSOR {
        uuid id PK
        uuid sync_def_id FK
        string cursor_scope
        string cursor_type
        string cursor_value
        uuid source_instance_id FK
        uuid target_list_id FK
        timestamp updated_at
    }

    SYNC_RUN {
        uuid id PK
        uuid sync_def_id FK
        string run_type
        string status
        timestamp start_time
        timestamp end_time
        int items_processed
        int items_failed
        string error_message
    }

    SYNC_METRIC {
        uuid id PK
        uuid sync_def_id FK
        uuid source_instance_id FK
        uuid target_list_id FK
        timestamp last_sync_ts
        bigint total_rows_synced
    }

    SOURCE_TABLE_METRIC {
        uuid id PK
        uuid table_id FK
        uuid database_instance_id FK
        timestamp captured_at
        bigint row_count
        timestamp max_updated_at
    }

    TARGET_LIST_METRIC {
        uuid id PK
        uuid target_list_id FK
        timestamp captured_at
        bigint item_count
        timestamp last_modified_at
    }
```

## Core Entity Relationships

### Inventory Layer
```mermaid
flowchart TB
    App[Application]
    DB[Database<br/>Logical]
    DBInst[Database Instance<br/>Physical]
    Table[Database Table]
    Column[Table Column]

    App -->|1:N| DB
    DB -->|1:N| DBInst
    DB -->|1:N| Table
    Table -->|1:N| Column

    SPConn[SharePoint Connection]
    Site[SharePoint Site]
    List[SharePoint List]
    SPCol[SharePoint Column]

    SPConn -->|1:N| Site
    Site -->|1:N| List
    List -->|1:N| SPCol

    style App fill:#e8f5e9
    style DB fill:#e8f5e9
    style DBInst fill:#e8f5e9
    style SPConn fill:#fce4ec
    style Site fill:#fce4ec
    style List fill:#fce4ec
```

### Sync Configuration Layer
```mermaid
flowchart TB
    SyncDef[Sync Definition]
    Table[Database Table]
    List[SharePoint List]

    Table -->|source_table_id| SyncDef
    List -->|target_list_id| SyncDef

    SyncDef -->|1:N| SyncSource[Sync Source<br/>Instance Binding]
    SyncDef -->|1:N| SyncTarget[Sync Target<br/>Multi-List Routing]
    SyncDef -->|1:N| FieldMap[Field Mapping<br/>Directional]
    SyncDef -->|1:N| KeyCol[Sync Key Column<br/>Composite Key]

    DBInst[Database Instance] -->|instance_id| SyncSource
    List2[SharePoint List] -->|target_list_id| SyncTarget
    SPConn[SharePoint Connection] -->|connection_id| SyncTarget

    style SyncDef fill:#fff3e0
    style Table fill:#e8f5e9
    style List fill:#fce4ec
    style DBInst fill:#e8f5e9
    style List2 fill:#fce4ec
```

### Runtime Sync Layer
```mermaid
flowchart TB
    SyncDef[Sync Definition]
    SyncDef -->|1:N| Ledger[Sync Ledger<br/>Provenance + Hash]
    SyncDef -->|1:N| Cursor[Sync Cursor<br/>Incremental State]
    SyncDef -->|1:N| Run[Sync Run<br/>History]
    SyncDef -->|1:N| Metric[Sync Metric<br/>Rollup Stats]

    Ledger -.->|tracks| DBInst[Database Instance]
    Cursor -.->|source_scope| DBInst
    Cursor -.->|target_scope| List[SharePoint List]

    style SyncDef fill:#fff3e0
    style Ledger fill:#e1f5ff
    style Cursor fill:#e1f5ff
    style Run fill:#c8e6c9
    style Metric fill:#c8e6c9
```

## Key Schema Patterns

### Multi-Source Support
```mermaid
flowchart LR
    SyncDef[Sync Definition]
    Source1[DB Instance 1<br/>PRIMARY<br/>priority=1]
    Source2[DB Instance 2<br/>SECONDARY<br/>priority=2]
    Source3[DB Instance 3<br/>SECONDARY<br/>priority=3]

    SyncDef -->|sync_sources| Source1
    SyncDef -->|sync_sources| Source2
    SyncDef -->|sync_sources| Source3

    Source1 -.->|failover| Source2
    Source2 -.->|failover| Source3

    style SyncDef fill:#fff3e0
    style Source1 fill:#c8e6c9
    style Source2 fill:#fff9c4
    style Source3 fill:#fff9c4
```

### Multi-Target Sharding
```mermaid
flowchart TB
    SyncDef[Sync Definition<br/>target_strategy=CONDITIONAL]
    Policy[Sharding Policy<br/>JSONB rules]

    Target1[Active Projects List<br/>is_default=true]
    Target2[Closed Projects List<br/>priority=2]
    Target3[Archived Projects List<br/>priority=3]

    SyncDef -->|sharding_policy| Policy
    SyncDef -->|sync_targets| Target1
    SyncDef -->|sync_targets| Target2
    SyncDef -->|sync_targets| Target3

    Policy -.->|if status='Active'| Target1
    Policy -.->|if status='Closed'| Target2
    Policy -.->|if age>365 days| Target3

    style SyncDef fill:#fff3e0
    style Policy fill:#ffecb3
    style Target1 fill:#c8e6c9
    style Target2 fill:#e1f5ff
    style Target3 fill:#fce4ec
```

### Directional Field Mapping
```mermaid
flowchart LR
    subgraph Source["Database Columns"]
        C1[project_code]
        C2[budget_amount]
        C3[created_by]
        C4[internal_notes]
    end

    subgraph Mappings["Field Mappings"]
        M1[BIDIRECTIONAL]
        M2[BIDIRECTIONAL]
        M3[PULL_ONLY]
        M4[PUSH_ONLY]
    end

    subgraph Target["SharePoint Columns"]
        T1[Title]
        T2[BudgetAmount]
        T3[CreatedBy]
        T4[InternalNotes]
    end

    C1 <-->|M1| T1
    C2 <-->|M2| T2
    C3 -->|M3| T3
    C4 -->|M4| T4

    style Source fill:#e8f5e9
    style Mappings fill:#fff3e0
    style Target fill:#fce4ec
```

## Index Strategy Visualization

```mermaid
flowchart TB
    subgraph Indexes["Critical Indexes"]
        I1[sync_ledger:<br/>UNIQUE ON sync_def_id,<br/>source_identity_hash]
        I2[sync_cursors:<br/>UNIQUE ON sync_def_id,<br/>cursor_scope,<br/>source_instance_id,<br/>target_list_id]
        I3[field_mappings:<br/>UNIQUE ON sync_def_id,<br/>source_column_id]
        I4[sync_targets:<br/>UNIQUE ON sync_def_id,<br/>target_list_id]
        I5[database_tables:<br/>UNIQUE ON database_id,<br/>schema_name, table_name]
    end

    subgraph Performance["Performance Indexes"]
        P1[sync_runs:<br/>INDEX ON sync_def_id,<br/>start_time DESC]
        P2[sync_ledger:<br/>INDEX ON sp_list_id,<br/>sp_item_id]
        P3[database_instances:<br/>INDEX ON database_id,<br/>status, priority]
    end

    style Indexes fill:#c8e6c9
    style Performance fill:#e1f5ff
```
