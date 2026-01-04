# Arcore SyncBridge Project Plan

Arcore SyncBridge is an enterprise-grade middleware platform that synchronizes PostgreSQL (system of record) with SharePoint/Teams lists via Microsoft Graph. It targets teams that need SQL-grade storage with SharePoint UX, providing reliable, bidirectional sync with comprehensive audit trails.

## Goals
- **Reliability**: Idempotent sync operations with durable audit trails and automatic retry logic
- **Operator Experience**: Intuitive UI for configuration, monitoring, and troubleshooting
- **Security**: Least-privilege access, encrypted credentials, and comprehensive audit logging
- **Scalability**: Horizontal scaling for large datasets with rate limiting and batching
- **Real-Time Sync**: CDC-based near real-time synchronization for critical data

## Scope (Implemented)
- ✅ Provision SharePoint lists and columns from Postgres schema
- ✅ Bidirectional sync (one-way push, two-way, and CDC) with sync ledger
- ✅ Sharding policies to route rows to multiple lists with dynamic moves
- ✅ Comprehensive admin UI for catalog, mapping, and run monitoring
- ✅ Run history dashboard with filtering and metrics
- ✅ Drift detection and reconciliation reporting
- ✅ Field mapping editor with directional control (BIDIRECTIONAL, PUSH_ONLY, PULL_ONLY)
- ✅ Type serialization for SharePoint API compatibility
- ✅ System field support (readonly SharePoint fields → writable DB columns)
- ✅ Cursor management with reset functionality
- ✅ Multi-source database support with failover
- ✅ Real-time CDC using PostgreSQL logical replication

## Scope (In Progress)
- 🔄 APScheduler integration for scheduled jobs
- 🔄 Scheduled jobs CRUD UI
- 🔄 Job monitoring and notifications

## Scope (Future Phases)
- Document library sync or file content replication
- Rich type transformation (Lookup ID↔Value, Person Email↔Name, Choice arrays)
- Data transformation rules (Upper, Lower, Trim, Regex) in mapping layer
- End-user report builders and self-service dashboards
- Secrets vault/KMS integration with rotation workflow
- Configuration audit logging and governance controls
- SSO roles and fine-grained RBAC (deferred to separate project)

## Architectural Principles
1. **Separation of Control and Data Planes**: Configuration API separate from sync workers
2. **Idempotent Operations**: Ledger-based tracking with content hashing ensures deterministic results
3. **Configuration as Data**: All configuration stored in meta-store, no hardcoded rules
4. **Security and Auditability**: Comprehensive logging, encrypted secrets, provenance tracking
5. **Fault Tolerance**: Automatic retries, graceful degradation, failover support

## Completed Milestones

### Phase 0: Foundation ✅
- Repository setup and standard layout
- CI/CD pipeline for lint and unit tests
- Meta-store schema with Alembic migrations
- Base FastAPI service with health endpoints
- Secrets management strategy (env + future vault/KMS)
- Observability baseline (structured logs, request IDs)
- Architecture diagrams (System Context, C4 Container)
- Success metrics definition (throughput, latency, error budget)

### Phase 1: Provisioning and One-Way Sync ✅
- Database instance management and health checks
- Schema introspection for tables, columns, constraints, indexes
- SharePoint connection profile management with per-connection credentials
- SharePoint list provisioning via Microsoft Graph
- SharePoint site/list discovery and selection
- Field mapping rules and type conversion
- Key strategy selection (PK, unique, composite)
- Cursor strategy and watermark column selection
- Sync ledger for idempotency
- Source cursor storage for incremental push
- Scheduled push sync with UPDATED_AT strategy
- Admin UI for connections and sync definitions
- End-to-end push sync worker with ledger upsert and Graph operations

### Phase 2: Sharding and Moves ✅
- Sharding policy evaluator with conditional multi-list routing
- Move logic (delete from old list + create in new list)
- UI for sharding rules configuration
- Ledger audit trail for move operations
- Drift detection reports (orphaned items, count mismatches)
- UI for drift reports
- Source failover and rebind workflow
- Per-definition SharePoint context (connection_id + site_id on SyncTarget)
- Scoped ledger entries by sync_def_id

### Phase 3: Two-Way Sync ✅
- Graph delta query ingestion for incremental pull
- Delta token persistence per list
- Conflict resolution policies (SOURCE_WINS, DESTINATION_WINS, LATEST_WINS)
- Loop prevention with ledger provenance (PUSH/PULL tracking)
- UI toggle for sync direction
- Integration test suite for bidirectional sync
- Push + ingress job wiring into scheduler and "Run Sync Now" UI
- Per-target SharePoint context storage
- Scoped cursors by source/target identifiers

### Phase 4: Hardening and Scale ✅
- Parallel worker pools with rate limit tuning
- Large-list batching and pagination
- Performance benchmarks and regression gates
- Disaster recovery runbook (Backup/Restore procedures)
- Release flow and rollback plan tested
- SSO roles and RBAC (deferred to separate project)

### Phase 5: Real-Time CDC and Governance ✅
- Published CDC strategy ADR (logical decoding, replication slots)
- CDC ingestion with LSN cursors and resumable checkpoints
- Backpressure, throttling, and pause/resume controls
- CDC event integration with mapping + sharding + move workflows
- Conflict resolution and loop prevention for CDC events
- Run history tables and APIs (sync_runs model, endpoints)
- Run history UI (/runs page with filtering, status, metrics)
- Operations endpoints for replication slot management
- Postgres permission validation
- Secrets vault/KMS (deferred - using env for now)
- Configuration audit logging (deferred to Phase 7)
- CDC end-to-end tests and perf gates (deferred to Phase 7)
- CDC lag monitoring UI (deferred to Phase 7)

### Phase 6: Advanced Mapping & Two-Way Fidelity ✅
- Interactive Mapping Editor UI with full CRUD in Sync Definition Detail
- System Field Ingress: Map readonly SharePoint fields to writable DB columns
- Directional Mapping: Per-field sync direction (PUSH_ONLY, PULL_ONLY, BIDIRECTIONAL)
- Type Serialization: Automatic datetime/Decimal/UUID to JSON conversion
- Field Mapping API: Dedicated CRUD endpoints (/field-mappings)
- Target Column Fetching: Load actual SharePoint columns with is_readonly detection
- Reset Cursor UI: "Reset Cursor" button for testing and recovery
- SharePoint GUID Resolution: Fixed UUID vs GUID bug in push sync
- Rich Type Support (deferred to Phase 7)
- Data Transformation (deferred to Phase 7)

## Current Milestone

### Phase 7: Scheduled Jobs & Automation 🔄
- [ ] Set up APScheduler for background job scheduling
- [ ] Create scheduled jobs CRUD UI (job schedules management)
- [ ] Add job status monitoring and notifications
- [ ] Implement job execution history and logs
- [ ] Add cron expression builder UI
- [ ] Support timezone-aware scheduling

## Dependencies
- ✅ Azure AD app registration with Microsoft Graph permissions
- ✅ SharePoint tenant and test site
- ✅ Source PostgreSQL connectivity with logical replication enabled
- ✅ PostgreSQL 13+ with pgcrypto extension and superuser access for CDC

## Risks and Mitigations
- **Graph API Throttling**: Implemented backoff, batching, and rate-limited workers ✅
- **Schema Drift**: Snapshots, diffing, and alerting mechanisms in place ✅
- **Conflict Handling**: Explicit policies with ledger provenance tracking ✅
- **Cursor Corruption**: Cursor reset functionality and advancement only on success ✅
- **Type Compatibility**: Automatic type serialization for SharePoint API ✅
- **Loop Prevention**: Provenance tracking prevents infinite bidirectional loops ✅
- **Database Failover**: Multi-source support with priority-based selection ✅
- **CDC Lag**: Backpressure controls and monitoring (monitoring UI deferred to Phase 7)

## Success Metrics (Current State)
- **Sync Throughput**: Successfully processing tables with 100K+ rows
- **Sync Latency**: Push sync completes in <5 minutes for incremental updates
- **Error Rate**: Failed items tracked per run with detailed error messages
- **Uptime**: Manual and scheduled sync operations with run history tracking
- **Data Fidelity**: Content hashing ensures accurate change detection
- **Audit Trail**: Complete ledger tracking of all synchronized rows
