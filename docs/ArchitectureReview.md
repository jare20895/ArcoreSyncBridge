# Architecture Review

## Repository Understanding

### Inferred Product Purpose
- Arcore SyncBridge is a control plane and worker system for synchronizing PostgreSQL tables with SharePoint lists over Microsoft Graph.
- Primary users are platform administrators, integration operators, and data operations teams.
- Core workflows are:
  - register source databases and instances
  - inventory source tables and SharePoint targets
  - define sync mappings and routing rules
  - run manual, scheduled, and CDC-driven syncs
  - inspect run history, drift, replication, and operational health

### Repo-Grounded Stack
- Frontend: Next.js pages router, React 18, TypeScript, Tailwind CSS, Axios, Lucide, React Flow, Mermaid.
- Backend: FastAPI, SQLAlchemy ORM, Alembic, Pydantic, psycopg/psycopg2, Celery, Redis.
- Data: PostgreSQL meta-store plus remote PostgreSQL source databases.
- Integrations: Microsoft Graph / SharePoint.

### Architecture Diagram
- Browser UI -> Next.js pages -> page-local state/effects -> `frontend/src/services/api.ts` -> FastAPI routers
- FastAPI routers -> service layer -> SQLAlchemy models / direct psycopg source DB access -> PostgreSQL meta-store / source DBs
- FastAPI -> Celery worker -> sync tasks -> Graph API / SharePoint
- FastAPI startup -> CDC manager -> CDC worker/process -> logical replication stream

### Current Architectural Style
- Split frontend/backend modular monolith with worker sidecars.

### Strengths
- Domain model is explicit and matches product intent.
- Workers are already separated from the API process.
- Inventory, sync definition, run history, drift, and CDC concepts all exist in code.
- Alembic migrations are present, so incremental schema evolution is viable.

### Architectural Debt
- No inbound authentication or authorization layer in the application.
- API, service, and DB dependency boundaries are inconsistent.
- Model, migration, and documentation drift is visible.
- Frontend is page-centric with little shared state or UI infrastructure.
- Deployment artifacts are still development-oriented.

## Repo Evidence

### Frontend
- Layout and navigation: `frontend/src/components/Layout.tsx`
- Dashboard: `frontend/src/pages/index.tsx`
- Sync definition detail: `frontend/src/pages/sync-definitions/[id].tsx`
- Runs UI: `frontend/src/pages/runs/index.tsx`
- API client: `frontend/src/services/api.ts`
- Theme tokens: `frontend/tailwind.config.ts`

### Backend
- App bootstrap and middleware: `backend/app/main.py`
- Config: `backend/app/core/config.py`
- Core sync models: `backend/app/models/core.py`
- Inventory models: `backend/app/models/inventory.py`
- CRUD and ops endpoints: `backend/app/api/endpoints/*`
- Push sync service: `backend/app/services/pusher.py`
- Ingress sync service: `backend/app/services/synchronizer.py`
- Source DB client: `backend/app/services/database.py`
- Worker tasks: `backend/app/worker/tasks.py`

### Infrastructure
- Compose runtime: `docker-compose.yml`
- Backend image: `backend/Dockerfile`
- Frontend image: `frontend/Dockerfile`
- Current GitHub automation: `.github/workflows/auto-pr.yml`

## Top Findings

### Critical
- No inbound app auth or RBAC.
- CORS is open to all origins.
- Secrets are stored directly in application tables.
- Source database SQL composition is unsafe.

### High
- Sync operations are triggered synchronously from API requests.
- Frontend has broken or placeholder navigation targets.
- Logging is not structured and mixes `logging` with `print`.
- CI quality gates are effectively absent.

### Medium
- Testing is thin and mostly mocked.
- Accessibility and interaction consistency are weak.
- Schema constraints and indexes are missing on key query paths.

## Target State
- Secure admin plane with Azure AD-backed auth and RBAC.
- Explicit module boundaries around inventory, sync, operations, and security.
- Async-first operations model for manual runs and retries.
- Standardized API envelopes, logging, telemetry, and audit trails.
- Shared frontend primitives for forms, dialogs, tables, filters, and feedback.
- Production-ready Docker and CI/CD pipeline with validation gates.

## Recommended Sequencing
1. Establish tooling and quality gates.
2. Lock down security baseline.
3. Normalize API contracts and shared UI primitives.
4. Move heavy operations to async orchestration.
5. Add constraints, indexes, and auditability.
6. Modernize operations UX and governance features.
