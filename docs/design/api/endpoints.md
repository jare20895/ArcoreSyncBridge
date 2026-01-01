# API Endpoints Specification

## Conventions
- Base URL: /api/v1
- Authentication: Bearer token in Authorization header
- Content-Type: application/json

## Health
- GET /health
- GET /version

## Connections
- GET /connections
- POST /connections
- GET /connections/{id}
- PATCH /connections/{id}
- POST /connections/{id}/verify

## Sync definitions
- GET /sync-definitions
- POST /sync-definitions
- GET /sync-definitions/{id}
- PATCH /sync-definitions/{id}
- POST /sync-definitions/{id}/provision

## Sync targets and routing rules
- GET /sync-definitions/{id}/targets
- POST /sync-definitions/{id}/targets
- PATCH /sync-definitions/{id}/targets/{target_id}
- DELETE /sync-definitions/{id}/targets/{target_id}
- GET /sync-definitions/{id}/routing-rules
- PUT /sync-definitions/{id}/routing-rules

## Sync runs
- POST /sync-definitions/{id}/run
- GET /sync-runs
- GET /sync-runs/{id}

## Ledger and diagnostics
- GET /sync-ledger
- GET /schema-snapshots
- GET /events

## Example: create sync definition
```json
{
  "name": "Projects Sync",
  "source_connection_id": "uuid",
  "dest_connection_id": "uuid",
  "source_schema": "public",
  "source_table": "projects",
  "sync_mode": "ONE_WAY_PUSH",
  "conflict_policy": "SOURCE_WINS",
  "target_strategy": "CONDITIONAL"
}
```

## Example: routing rules payload
```json
{
  "rules": [
    {"if": "status == 'Active'", "target_list_id": "list-active-id"},
    {"if": "status == 'Closed'", "target_list_id": "list-closed-id"},
    {"if": "age_days >= 365", "target_list_id": "list-archived-id"}
  ],
  "default_target_list_id": "list-active-id"
}
```
