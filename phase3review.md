# Phase 3 Review

## Scope
- Reviewed checklist/specs: `docs/PHASED_CHECKLIST.md`, `docs/IMPLEMENTATION_SPECS.md`
- Code paths: `backend/app/services/synchronizer.py`, `backend/app/services/pusher.py`, `backend/app/services/sharepoint_content.py`, `backend/app/api/endpoints/ops.py`, `backend/app/models/core.py`, `backend/app/schemas/sync_definition.py`, `backend/alembic/versions/*`, `frontend/src/pages/sync-definitions/*`, `backend/tests/services/test_integration_twoway.py`
- Focus: Phase 3 (Two-Way Sync)

## Summary
- Two-way sync has delta ingestion, a pusher service, and an ingress endpoint, but the pipeline is not fully wired or correct.
- Conflict resolution and loop prevention are incomplete; cursor scoping and model/migration alignment block per-list delta tokens.
- UI exposes TWO_WAY selection, but the toggle is not connected to API behavior.

## Phase 3 Review

### Implemented (partial)
- Graph delta query ingestion + pagination: `backend/app/services/sharepoint_content.py`
- Ingress flow via `/ops/ingress/{sync_def_id}`: `backend/app/api/endpoints/ops.py`, `backend/app/services/synchronizer.py`
- Push flow with ledger-based loop prevention logic (not scheduled): `backend/app/services/pusher.py`
- UI selection for TWO_WAY and a mode toggle (UI-only): `frontend/src/pages/sync-definitions/new.tsx`, `frontend/src/pages/sync-definitions/[id].tsx`
- Mocked two-way tests (not end-to-end): `backend/tests/services/test_integration_twoway.py`

### Gaps / Issues
- [High] Conflict resolution is stubbed; ingress updates source even when `conflict_policy == "SOURCE_WINS"`. `backend/app/services/synchronizer.py`
- [High] Delta token persistence is not per list: `SyncCursor` lacks `target_list_id` and its PK is only `(sync_def_id, cursor_scope)`, but synchronizer writes `target_list_id`. `backend/app/services/synchronizer.py`, `backend/app/models/core.py`
- [High] Two-way pipeline is not scheduled or wired (Celery + UI “Run Sync Now” are not connected to `Pusher`/`Synchronizer`). `backend/app/worker/tasks.py`, `frontend/src/pages/sync-definitions/[id].tsx`
- [High] SharePoint context is not per-definition; ingress/push use env `SHAREPOINT_SITE_ID` and the first active connection. `backend/app/services/synchronizer.py`, `backend/app/services/pusher.py`
- [Medium] Key strategy, cursor column selection, and field mapping names are not persisted via API/migrations; `Pusher`/`Synchronizer` rely on fields that are not in schema/migrations. `backend/app/schemas/sync_definition.py`, `backend/app/models/core.py`, `backend/alembic/versions/001_initial_schema.py`
- [Medium] Cursor strategy uses hardcoded `updated_at`, ignores `cursor_column_id`, and hashes only a single key value. `backend/app/services/pusher.py`
- [Low] Tests cover mocked flows only; no integration test suite across both directions as specified. `backend/tests/services/test_integration_twoway.py`
- [Low] CursorService still uses the old composite PK; with surrogate IDs, `db.get` won't resolve cursors reliably. `backend/app/services/state.py`

## Cross-Cutting Data Model / Migration Gaps
- `SyncDefinition.source_schema`/`source_table_name` and `FieldMapping.source_column_name`/`target_column_name` exist in ORM but not in migrations or API schemas.
- `SyncLedgerEntry` is not scoped by `sync_def_id`, risking collisions across definitions in two-way sync.
- Migration `003_fix_models` uses `gen_random_uuid()` without enabling pgcrypto; fresh Postgres installs will fail that migration. `backend/alembic/versions/003_fix_models.py`

## Design Recommendations
- Store SharePoint context on `SyncTarget` (`sharepoint_connection_id`, `site_id`) and use it in ingress/push.
- Scope cursors per source instance and per target list (separate tables or composite keys).
- Implement conflict resolution policies using ledger content hashes + provenance, and only overwrite when appropriate.
- Align migrations and API schemas with ORM fields used by two-way services.

## Suggested Next Steps (Phase 3 Completion)
- Wire `Pusher` + `Synchronizer` into scheduled jobs and the “Run Sync Now” UI.
- Implement conflict resolution and loop prevention end-to-end (per spec).
- Fix cursor scoping and delta token persistence per list.
- Add integration tests that validate push + pull flows together.
