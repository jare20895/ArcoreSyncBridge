# Arcore SyncBridge Phased Implementation Checklist

This checklist tracks delivery by phase. Items can be moved forward as scope evolves.

## Phase 0: Foundation
- [x] Repository setup and standard layout
- [x] CI pipeline for lint and unit tests
- [x] Base FastAPI service with health endpoints
- [x] Meta-store schema migrations (apps, databases, instances, SharePoint connections, ledger)
- [ ] Ensure sync_cursors UUID defaults work in Postgres (pgcrypto or app-side UUIDs)
- [x] Secrets management strategy (env + vault/KMS)
- [x] Observability baseline (structured logs, request IDs)
- [x] Finalize Architecture Diagrams (System Context, C4 Container)
- [x] Define Success Metrics (throughput, latency, error budget)

## Phase 1: Provisioning and One-Way Sync
- [x] Database instance management and health checks
- [ ] Schema introspection for tables, columns, constraints, indexes
- [x] SharePoint connection profile management
- [ ] Use SharePointConnection.client_secret as primary auth source (env fallback for local dev)
- [x] SharePoint list provisioning via Graph
- [x] SharePoint site/list discovery and selection
- [x] Field mapping rules and type conversion
- [x] Key strategy selection and validation (PK, unique, composite)
- [x] Cursor strategy and watermark column selection
- [x] Sync ledger write/read for idempotency
- [x] Source cursor storage for incremental push
- [ ] Scheduled push sync (updated_at strategy)
- [x] Admin UI for connections and sync definitions
- [x] Store database credentials on DatabaseInstance (db_name, user, password) with vault-migration note
- [x] Implement end-to-end push sync worker (source selection, cursor read/write, ledger upsert, Graph create/update)
- [ ] Use DatabaseInstance credentials in DB client/introspection/connection tests
- [ ] Expose DatabaseInstance credentials in API schemas/UI
- [ ] Persist source schema/table name and field mapping names via API
- [ ] Use cursor_column_id for UPDATED_AT queries
- [ ] Persist field mappings and sync targets during provisioning
- [x] Align ORM models and migrations for Phase 1 fields
- [ ] Define Accessibility targets for Admin UI

## Phase 2: Sharding and Moves
- [x] Sharding policy evaluator (conditional multi-list routing)
- [x] Move logic (delete old list + create new)
- [x] UI for sharding rules
- [x] Ledger audit trail for moves
- [x] Drift detection report (orphaned items)
- [x] UI for Drift Reports
- [x] Source failover and rebind workflow
- [ ] Store SharePoint connection_id + site_id on SyncTarget (per-definition context)
- [ ] Scope SyncLedgerEntry by sync_def_id (unique per definition)
- [ ] Apply sharding automatically for target_strategy=CONDITIONAL; allow per-run override for single target
- [ ] Remove env-based SharePoint context from moves/drift

## Phase 3: Two-Way Sync
- [x] Graph delta query ingestion
- [x] Persist delta tokens per list
- [x] Conflict resolution policies
- [x] Loop prevention (ledger provenance)
- [x] UI toggle for sync direction
- [ ] Integration test suite across both directions
- [ ] Wire push + ingress jobs into scheduler and UI "Run Sync Now"
- [ ] Store SharePoint context per target (connection_id, site_id) and remove env-based context
- [ ] Scope cursors by source/target identifiers to support per-list delta tokens
- [ ] Align ORM fields (source_schema/table_name, field mapping names) with migrations and API schemas
- [ ] Update CursorService to use SyncCursor surrogate ID + scoped indexes

## Phase 4: Hardening and Scale
- [x] Parallel worker pools and rate limit tuning
- [x] Large-list batching and pagination
- [x] Performance benchmarks and regression gates
- [ ] SSO roles and fine-grained RBAC (Deferred to separate project)
- [x] Disaster recovery runbook (Backup/Restore)
- [x] Release flow and Rollback plan tested
