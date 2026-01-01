# Arcore SyncBridge Phased Implementation Checklist

This checklist tracks delivery by phase. Items can be moved forward as scope evolves.

## Phase 0: Foundation
- [x] Repository setup and standard layout
- [x] CI pipeline for lint and unit tests
- [x] Base FastAPI service with health endpoints
- [x] Meta-store schema migrations (apps, databases, instances, SharePoint connections, ledger)
- [x] Secrets management strategy (env + vault/KMS)
- [x] Observability baseline (structured logs, request IDs)
- [x] Finalize Architecture Diagrams (System Context, C4 Container)
- [x] Define Success Metrics (throughput, latency, error budget)

## Phase 1: Provisioning and One-Way Sync
- [x] Database instance management and health checks
- [x] Schema introspection for tables, columns, constraints, indexes
- [x] SharePoint connection profile management
- [x] SharePoint list provisioning via Graph
- [x] SharePoint site/list discovery and selection
- [x] Field mapping rules and type conversion
- [x] Key strategy selection and validation (PK, unique, composite)
- [x] Cursor strategy and watermark column selection
- [x] Sync ledger write/read for idempotency
- [x] Source cursor storage for incremental push
- [x] Scheduled push sync (updated_at strategy)
- [x] Admin UI for connections and sync definitions
- [ ] Define Accessibility targets for Admin UI

## Phase 2: Sharding and Moves
- [ ] Sharding policy evaluator (conditional multi-list routing)
- [ ] Move logic (delete old list + create new)
- [ ] UI for sharding rules
- [ ] Ledger audit trail for moves
- [ ] Drift detection report (orphaned items)
- [ ] Source failover and rebind workflow

## Phase 3: Two-Way Sync
- [ ] Graph delta query ingestion
- [ ] Persist delta tokens per list
- [ ] Conflict resolution policies
- [ ] Loop prevention (ledger provenance)
- [ ] UI toggle for sync direction
- [ ] Integration test suite across both directions

## Phase 4: Hardening and Scale
- [ ] Parallel worker pools and rate limit tuning
- [ ] Large-list batching and pagination
- [ ] Performance benchmarks and regression gates
- [ ] SSO roles and fine-grained RBAC
- [ ] Disaster recovery runbook (Backup/Restore)
- [ ] Release flow and Rollback plan tested

