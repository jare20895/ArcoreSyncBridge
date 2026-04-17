# Application Intelligence Document (AID)

Application: ArcoreSyncBridge
Repository: ArcoreSyncBridge
Version: 1.0.0
Generated: 2026-04-17
Document Type: Application Intelligence Document (AID)

Purpose:
Provide a comprehensive system-level understanding of the application including architecture, features, APIs, workflows, and data models so engineers and AI systems can analyze, improve, and extend the system.

---

## 1 Executive Overview

ArcoreSyncBridge is a **High-Performance Two-Way Synchronization Engine** designed specifically bridging PostgreSQL internal relational data with Microsoft SharePoint via the MS Graph API. It ensures that complex structured data living deep inside PostgreSQL databases stays in perfect harmony with SharePoint Lists (and conversely) with extremely low latency and strict idempotency controls.

### Primary Users
- **Data Engineers & Architects**: Designing zero-downtime replication pipelines where enterprise reporting depends heavily on Microsoft SharePoint frontends but truth lives in Postgres backends.
- **Enterprise Operations**: Operating a safe control plane to manage replication slots, publications, and conflict resolution schemas visually.

### High-Level Capabilities
- **Change Data Capture (CDC)**: Utilizes native PostgreSQL Logical Replication (`pgoutput`) and replication slots to consume Write-Ahead Logs (WAL) natively, detecting row inserts/updates without brutal polling workloads.
- **Bi-Directional Conflict Resolution**: Native `DESTINATION_WINS` and `SOURCE_WINS` logic built-in to handle simultaneous edits on both the Postgres and SharePoint endpoints.
- **Loop Prevention Mechanisms**: Hardened internal Ledger caching (hash & provenance checking) to ensure pushing a row to SharePoint doesn't accidentally trigger a webhook that writes it back down to Postgres in an infinite loop.
- **Delta Query Integration**: Specifically optimized for the Microsoft Graph API's `/delta` endpoints to fetch only newly modified SharePoint items efficiently during ingress tracking.

### Architectural Summary
The system uses a **FastAPI** Python control plane backed by an embedded SQLAlchemy ORM configuration. **Alembic** manages the internal configuration state while multiple backend worker services actually ingest the CDC streams (`CDCConsumer`), handle external API pagination (`SharePointContentService`, `graph.py`), and handle concurrency push operations (`Pusher`, `Synchronizer`). A **Vite/React** frontend provides a visual control panel to map schemas, map database instances natively, and flip Two-Way sync toggles on the fly. 

---

## 2 Repository / System Overview

```
ArcoreSyncBridge/
├── backend/
│   ├── alembic/               # Database migration versions
│   ├── app/
│   │   ├── api/               # FastAPI controllers and router groupings
│   │   ├── core/              # Config, Security, and exception logic
│   │   ├── db/                # SQLAlchemy session definitions
│   │   ├── models/            # State machine (core.py, inventory.py, platform.py)
│   │   ├── services/          # Real business logic (pusher.py, synchronizer.py)
│   │   └── schemas/           # Pydantic input validations
│   └── tests/
├── frontend/                  # React + Vite dashboard
│   └── src/
├── docs/                      # Architectural feature specifications
└── docker-compose.yml         # Container mapping execution environments
```

---

## 3 Technology Stack

### 3.1 Backend Control & Pipeline Execution (`backend/app`)
| Technology | Purpose |
|---|---|
| Python & FastAPI | Primary execution and control plane exposed for configuration |
| SQLAlchemy 2.0 & Alembic | Heavy state-machine relational tracking for cursors and sync ledgers |
| `psycopg2` | Raw PostgreSQL interaction natively connecting to external targets for DB Introspection and CDC replication slot listening |

### 3.2 Microsoft Integration
| Technology | Purpose |
|---|---|
| MS Graph API | Natively maps Database tables to generic SharePoint Custom Lists, tracking List item IDs back to source Database UUIDs. |

### 3.3 Frontend GUI (`frontend`)
| Technology | Purpose |
|---|---|
| React 18 & Vite | Visual Dashboard allowing ops engineering to toggle `DESTINATION_WINS`, toggle One-Way vs Two-Way syncing, and map Column A to Column B without touching code. |

---

## 4 Application Architecture

### 4.1 Automated Logical Replication (Outbound/Push)
When configured via the UI, a `DatabaseInstance` creates a formal PostgreSQL *Publication*.
1. **Introspection**: `introspection.py` connects to the DB, reads all tables and columns, surfacing them in the UI.
2. **Setup**: The UI assigns a `replication_slot_name` to the Database Instance. The `PublicationManager` issues `CREATE PUBLICATION` on the target database, pointing to the designated tables.
3. **Execution**: The `cdc_consumer.py` uses asynchronous streaming to listen to the replication slot. When an OS-level write to Postgres occurs, it picks up the row ID.
4. **Push**: The `pusher.py` formats the PostgreSQL schema output into a generic MS Graph schema based on the bound `FieldMapping`, passing structural diffs to SharePoint.

### 4.2 Webhook / Delta Graph Queries (Inbound/Pull)
When an edit occurs in SharePoint:
1. **Delta Pull**: `Synchronizer` calls Graph Delta endpoints to fetch all changed items.
2. **Loop Prevention Validation**: The system checks the internal ledger. If the incoming change was strictly an echo initiated by the `Pusher` a microsecond earlier, it drops the record.
3. **Reconciliation**: If valid, the system respects the Conflict Resolution Policy (e.g. `DESTINATION_WINS`) and converts the SharePoint entry row format back into a PostgreSQL `UPDATE` statement, firing it directly against the source database.

---

## 5 Feature Inventory

### 5.1 One-Way Provisioning & One-Way Push
- **Status**: Complete
- **Description**: Exposes endpoints to CRUD Database Instances and SharePoint Connections. Handles standard `INSERT`, `UPDATE`, `DELETE` operations detected via CDC and reflects them cleanly into SharePoint.
- **Module**: `cdc.py`, `pusher.py`

### 5.2 Two-Way Sync Engine & Conflict Management
- **Status**: Complete
- **Description**: Features Native MS Graph Delta queries and Ingress persistence, supporting `DESTINATION_WINS` logic explicitly using `Synchronizer`. Fallbacks are included to infer database instances from Table IDs securely if tracking definitions are decoupled.
- **Module**: `synchronizer.py`, `sharepoint_content.py`

### 5.3 Safe Loop Prevention
- **Status**: Complete
- **Description**: Advanced Ledger implementation using cryptographic hashing and `provenance` UUIDs. Eliminates the catastrophic "Ping-Pong" loop scenario where Postgres updates SharePoint, which triggers a webhook, which updates Postgres, infinitely. 
- **Module**: `pusher.py`, `reconciliation.py`

### 5.4 High-Performance CDC Consumer Optimization
- **Status**: Complete
- **Description**: Implements logical backpressure fixes checking `maxlen` instead of strict fixed lengths explicitly to prevent Deadlocks. Drops arbitrary unassigned slots dynamically when tracking definitions change to preserve disk space on target databases.
- **Module**: `cdc_consumer.py`, `cdc_manager.py`

---

## 6 Known Gaps and Technical Debt

1. **Replication Connection Load**: Directly attaching `cdc_consumer` listeners strictly inside a Python FastAPI thread/worker loop without robust multiplexing can result in dropped events during massive restart patches or scale-out issues if multiple pods attempt to read the same slot.
2. **Missing Sharding Capability**: The source code shows early `sharding.py` files. True cross-regional synchronization across millions of rows requires data-sharding which is indicated but heavily underutilized structurally. 

---

## 7 LLM-Ready System Understanding Summary

ArcoreSyncBridge is a **Bi-Directional Database-to-SharePoint Synchronization Engine**. 

It uses raw PostgreSQL WAL logs (`pgoutput`) to track database mutations and Microsoft Graph API `/delta` queries to track SharePoint mutations. If fixing or modifying the pipeline, you must deeply respect the `provenance` hashes and loop-prevention checks located within the `Synchronizer` and `Pusher` components—they are the critical defense preventing the system from DDOSing itself through infinite event bouncing.
