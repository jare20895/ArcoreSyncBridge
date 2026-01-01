# Arcore SyncBridge Project Plan

Arcore SyncBridge is a middleware platform that synchronizes PostgreSQL (system of record) with SharePoint/Teams lists via Microsoft Graph. It targets teams that need SQL-grade storage with SharePoint UX.

## Goals
- Reliable, idempotent sync with a durable audit trail.
- Operator-friendly configuration and monitoring.
- Secure by default with least-privilege access.
- Horizontal scalability for large datasets.

## Scope (in)
- Provision SharePoint lists and columns from Postgres schema.
- One-way and two-way sync with a sync ledger.
- Sharding policies to route rows to multiple lists.
- UI for catalog, mapping, and run monitoring.
- Observability and run history.

## Scope (out, for now)
- Document library sync or file content replication.
- Real-time CDC streaming (planned for a later phase).
- End-user report builders.

## Architectural principles
1. Separation of control plane and data plane.
2. Idempotent operations with deterministic mapping.
3. Configuration as data stored in the meta-store.
4. Security and auditability as first-class requirements.

## Milestones
- Phase 0: Foundation (repo, CI/CD, meta-store schema, API skeleton)
- Phase 1: Provisioning and one-way push sync
- Phase 2: Sharding and list move logic
- Phase 3: Two-way sync and conflict resolution
- Phase 4: Performance tuning and enterprise hardening

## Dependencies
- Azure AD app registration with Graph permissions.
- SharePoint tenant and test site.
- Source Postgres connectivity.

## Risks and mitigations
- Graph API throttling: backoff, batching, and queue-based workers.
- Schema drift: snapshots, diffing, and alerting.
- Conflict handling: explicit policy and ledger provenance tracking.
