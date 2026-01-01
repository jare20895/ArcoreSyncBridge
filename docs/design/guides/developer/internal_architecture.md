# Internal Architecture

## Codebase structure (planned)
- api/: FastAPI control plane
- workers/: Celery tasks for sync
- core/: Mapping, sharding, ledger, and policy logic
- connectors/: Graph and Postgres clients
- ui/: Next.js admin console
- docs/: Documentation

## Key modules
- Mapping Engine: field transformations and type coercion
- Ledger Service: idempotency and conflict tracking
- Provisioner: Postgres schema to SharePoint list creation
- Orchestrator: schedules and dispatches sync jobs
