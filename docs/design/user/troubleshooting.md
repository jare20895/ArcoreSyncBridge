# Troubleshooting Guide

## Common issues

### Graph permission errors
- Ensure the Azure AD app has Sites.ReadWrite.All or equivalent.
- Verify admin consent has been granted.

### Throttling
- Graph responses include Retry-After.
- Reduce worker concurrency or batch size.

### Schema mismatch
- Re-run provisioning to add missing columns.
- Verify field mappings for renamed columns.

### Drifted records
- Check the drift report and reconcile manual edits.
- Re-run push sync to restore authoritative data.
