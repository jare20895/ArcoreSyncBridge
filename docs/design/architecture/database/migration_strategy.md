# Database Migration Strategy

## Version control
- Use Alembic for schema migrations.
- Every change to meta-store tables must include a migration script.

## Zero-downtime approach
1. Add new columns as nullable.
2. Deploy application updates that write both old and new columns.
3. Backfill data in background jobs.
4. Enforce constraints and remove old columns in later releases.

## Rollback
- Keep down migrations for non-destructive changes.
- For destructive changes, provide a forward fix and data restore procedure.
