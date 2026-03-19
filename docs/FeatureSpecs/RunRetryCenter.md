# Feature Spec: Run Retry Center

## Goal
- Let operators recover from failed sync executions without leaving the operations workspace.

## Scope
- Retry failed runs
- Requeue stuck runs
- Capture retry reason
- Track retry lineage

## Acceptance Criteria
- User can retry a failed run
- System records retry reason and actor
- Retries are idempotent
- UI shows original run and retry chain
- Duplicate concurrent retries are blocked
- Retry status is visible in the run detail view

## API Changes
- Retry enqueue endpoint
- Retry lineage query

## Data Changes
- `retry_of_run_id` on `sync_runs`
- audit entries for retries
