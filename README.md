# Arcore SyncBridge

Arcore SyncBridge is a middleware service that synchronizes PostgreSQL data with SharePoint/Teams lists using Microsoft Graph. It provides a control plane API and UI for configuration, a worker-based data plane for sync jobs, and a meta-store that tracks state and audit history.

## Core capabilities
- Provision SharePoint lists and columns from Postgres schemas
- One-way and two-way sync with idempotent ledger tracking
- Sharding policies that route rows to multiple lists
- Drift detection, run history, and operational dashboards

## Architecture overview
- Control plane API: FastAPI (Python)
- Data plane workers: Celery + Redis
- Meta-store: PostgreSQL
- UI: Next.js
- External systems: Microsoft Graph + SharePoint + Azure AD

## Documentation
- docs/PROJECT_PLAN.md
- docs/IMPLEMENTATION_SPECS.md
- docs/DATA_MODEL.md
- docs/UI_UX_DESIGN.md
- docs/design/architecture/README.md
- docs/design/api/README.md

## Status
Design and development phase. Phase 1 focuses on provisioning and one-way sync.
