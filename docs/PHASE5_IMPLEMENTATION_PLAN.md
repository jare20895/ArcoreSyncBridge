# Phase 5 Implementation Plan (Epics and Tickets)

Phase 5 focuses on real-time CDC ingestion, unified change processing, and enterprise-grade governance/operations.

## Prerequisites
- Phase 3/4 blockers resolved: per-target SharePoint context, scheduler wiring, conflict resolution, safe migrations.
- Baseline run history and metrics endpoints exist for the current push/ingress pipeline.

## Epic 1: CDC Strategy and Foundations
- P5-01: Publish ADR selecting CDC approach (logical decoding vs Debezium) and slot management strategy.
- P5-02: Extend metadata for CDC cursors (LSN) and add indexes for per-source/per-target cursor scoping.
- P5-03: Add ops endpoints to create/inspect/drop replication slots and validate required Postgres permissions.

## Epic 2: CDC Ingestion Service
- P5-04: Implement CDC reader with checkpointing into SyncCursor (LSN) and resumable offsets.
- P5-05: Introduce a buffer/queue between CDC reader and Graph writes (batching + retry).
- P5-06: Add backpressure controls (pause/resume per sync definition) and throttle handling.

## Epic 3: Unified Change Pipeline
- P5-07: Normalize CDC events into the existing mapping/transform pipeline (field mappings + type rules).
- P5-08: Apply sharding and move logic for CDC events (create/update/move/delete) with ledger updates.
- P5-09: Extend conflict resolution to CDC events and enforce loop-prevention semantics.

## Epic 4: Observability and Run History
- P5-10: Add run history tables and APIs (sync_runs, sync_run_metrics, reconcile stats).
- P5-11: Emit metrics for CDC lag, throughput, errors, and retries; wire dashboards.
- P5-12: UI for CDC status, lag, and job control (start/stop, last run summary).

## Epic 5: Security and Governance
- P5-13: Move secrets to vault/KMS and implement rotation workflow for SharePoint + DB creds.
- P5-14: Add audit log for configuration changes with user attribution.
- P5-15: Add role-based access control for connections/definitions (if in scope for Phase 5).

## Epic 6: Test, Hardening, and Release
- P5-16: CDC end-to-end integration tests (push, pull, conflict, failover).
- P5-17: Load/perf testing for CDC streams with regression gates.
- P5-18: Update DR and rollback guides for replication slots and CDC cursors.

## Success Criteria
- P95 end-to-end change propagation latency within agreed SLA (e.g., <60s).
- No duplicate writes across restart/replay; cursor checkpoints are consistent.
- CDC lag alerting and recovery playbooks validated in staging.
