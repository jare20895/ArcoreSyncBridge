# ADR 001: Hub-and-Spoke Sync Architecture

## Status
Accepted

## Context
The platform must synchronize PostgreSQL (system of record) with SharePoint lists while avoiding Dataverse limits. Direct client integrations would be brittle, hard to audit, and unable to manage long-running sync jobs.

## Decision
Adopt a hub-and-spoke architecture with a control plane and data plane:
- Control plane (FastAPI + UI) manages configuration, provisioning, and orchestration.
- Data plane (Celery workers + Redis) executes sync jobs and handles retries.
- A meta-store (Postgres) provides a durable sync ledger and audit trail.

## Consequences
- Additional infrastructure components are required (queue, workers).
- Clear separation of responsibilities enables safe scaling and isolation.
- The ledger becomes the authoritative source for idempotency and conflict control.
