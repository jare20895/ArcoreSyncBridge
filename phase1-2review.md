# Phase 1-2 Review

## Scope
- Reviewed checklist/specs: `docs/PHASED_CHECKLIST.md`, `docs/IMPLEMENTATION_SPECS.md`
- Code paths: `backend/app/api/endpoints/*`, `backend/app/services/*`, `backend/app/models/core.py`, `backend/alembic/versions/*`, `frontend/src/pages/*`, `frontend/src/services/api.ts`
- Focus: Phase 1 (Provisioning + one-way push) and Phase 2 (Sharding + moves)

## Summary
- Phase 1 has CRUD and Graph plumbing, but the actual push sync pipeline (cursoring, ledger idempotency, scheduled runs) is not implemented end-to-end.
- Phase 2 has sharding evaluation and move/drift scaffolding, but lacks correct SharePoint context per definition and is not wired into sync execution.
- Data model and migrations are out of sync in several places, which will block Phase 1/2 behavior as written in the specs.

## Phase 1 Review

### Implemented (partial)
- Database instance CRUD and health check endpoints: `backend/app/api/endpoints/database_instances.py`
- Basic schema introspection (tables/columns/PKs only): `backend/app/services/introspection.py`
- SharePoint connection CRUD: `backend/app/api/endpoints/sharepoint_connections.py`
- SharePoint discovery/provisioning endpoints + type mapping: `backend/app/api/endpoints/sharepoint_discovery.py`, `backend/app/services/provisioner.py`
- Admin UI for connections + sync definition CRUD: `frontend/src/pages/sharepoint-connections/new.tsx`, `frontend/src/pages/sync-definitions/*`

### Gaps / Issues
- [High] Push sync workflow is stubbed; no source selection, cursoring, ledger use, or Graph writes. `backend/app/worker/tasks.py`
- [High] Cursor strategy stored but not implemented; no per-source cursor storage. `backend/app/models/core.py`, `backend/app/services/state.py`
- [High] Ledger idempotency is not used in push sync; ledger writes only appear in move path. `backend/app/services/mover.py`
- [High] Introspection uses hardcoded credentials/db name and only collects PKs; no constraints/indexes or snapshot persistence. `backend/app/services/introspection.py`
- [High] Database client uses hardcoded credentials/db name; DatabaseInstance credentials are not used by the client yet. `backend/app/services/database.py`, `backend/app/schemas/database_instance.py`
- [Medium] SharePoint provisioning uses placeholder secret logic and does not persist field mappings/targets to the meta-store. `backend/app/api/endpoints/provisioning.py`
- [Medium] UI does not support field mapping, key strategy validation, or cursor selection workflows described in specs. `frontend/src/pages/sync-definitions/new.tsx`
- [Low] Accessibility targets for Admin UI are not defined (checklist item). `docs/PHASED_CHECKLIST.md`

## Phase 2 Review

### Implemented (partial)
- Sharding policy evaluator: `backend/app/services/sharding.py`
- Move logic (create -> ledger -> delete) + audit log: `backend/app/services/mover.py`, `backend/app/services/state.py`, `backend/alembic/versions/70043344a3d8_add_move_audit_log.py`
- Drift report (ledger validity): `backend/app/services/drift.py`, UI in `frontend/src/pages/sync-definitions/[id].tsx`
- Failover + rebind of sync sources: `backend/app/services/failover.py`

### Gaps / Issues
- [High] Sharding evaluator is not integrated into a sync pipeline (no routing during push runs). `backend/app/worker/tasks.py`
- [High] Moves and drift rely on env-based `SHAREPOINT_SITE_ID` and first active connection, not per-definition context. `backend/app/api/endpoints/moves.py`, `backend/app/services/drift.py`
- [Medium] Drift checks only "ledger -> SP missing" and do per-item Graph calls; no "SP -> ledger missing" or batching. `backend/app/services/drift.py`
- [Medium] Failover does not enforce a single PRIMARY per sync definition; cursor reset/consistency handling is not addressed. `backend/app/services/failover.py`
- [Low] UI for sharding rules is JSON-only; no rule builder or list validation. `frontend/src/pages/sync-definitions/new.tsx`

## Cross-Cutting Data Model / Migration Gaps
- [High] ORM adds fields not present in migrations (e.g., `source_schema`, `source_table_name`, `source_column_name`, `target_column_name`). `backend/app/models/core.py`, `backend/alembic/versions/001_initial_schema.py`
- [High] `SyncCursor` primary key is only `(sync_def_id, cursor_scope)`, which prevents per-source/per-target cursoring needed for sharding and failover. `backend/app/models/core.py`, `backend/app/services/state.py`

## Design Recommendations
- Store SharePoint context on `SyncTarget` (`sharepoint_connection_id`, `site_id`) and optionally mirror defaults on `SyncDefinition` for UI display.
- Scope ledger and cursors by `sync_def_id` plus source/target identifiers:
  - Ledger unique key: `(sync_def_id, source_identity_hash)` plus a unique index on `(sync_def_id, sp_list_id, sp_item_id)`.
  - Cursor: split into source/target cursor tables or add `target_list_id` and unique constraints per scope.
- Align migrations with models before building the push sync pipeline.

## Suggested Next Steps (Phase 1-2 Completion)
- Implement push sync workflow: source selection, cursor reads/writes, ledger idempotency, sharding routing, Graph upserts.
- Move secrets/credentials into `DatabaseInstance` as agreed; add secure storage notes for future vault migration.
- Wire move + drift to `SyncTarget` context instead of env vars.
- Add tests for provisioning, sync pipeline, drift, and moves endpoints.
