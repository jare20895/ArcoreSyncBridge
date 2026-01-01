# Operational Runbook

This runbook covers routine tasks and incident responses for Arcore SyncBridge.

## Routine tasks

### Backups
- Frequency: Daily
- Target: Meta-store Postgres
- Verify: Restore to staging weekly

### Secret rotation
- Frequency: Quarterly or on incident
- Rotate: Azure AD client secrets and DB credentials
- Validate: Re-run connection verification

### Queue health
- Monitor queue depth and worker lag
- Scale workers when queue depth exceeds thresholds

## Common incidents

### Graph API throttling
- Symptom: 429 responses with Retry-After headers
- Action: Reduce concurrency, increase backoff, reschedule jobs

### Sync failures for a definition
- Symptom: Repeated errors for a single sync definition
- Action: Pause the definition, review ledger and events, re-run after fix

### Postgres connectivity loss
- Symptom: Connection timeouts
- Action: Fail fast notice, retry with exponential backoff, notify on-call
