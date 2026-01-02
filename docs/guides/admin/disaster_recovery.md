# Disaster Recovery Runbook

This guide outlines the procedures for backing up and restoring the Arcore SyncBridge system.

## Data Classification
- **Critical Data:** 
    - PostgreSQL Database (`arcore_syncbridge`): Contains Sync Definitions, Mappings, Connection Configs, Ledger, and Cursors.
    - Environment Variables (`.env`): Contains Secrets (DB passwords, Azure Client Secrets).
- **Transient Data:**
    - Redis: Task queues (can be drained/flushed).
    - Application Code: Recoverable from Git.

## Backup Procedure

### Automated Database Backup
Use the provided script `scripts/backup_db.sh`. Ideally, configure this as a daily cron job.

```bash
cd /path/to/project
./scripts/backup_db.sh
```

**Artifacts:**
- `backups/backup_arcore_syncbridge_YYYYMMDD_HHMMSS.sql.gz`

### Configuration Backup
Ensure the `.env` file or your Secret Management (e.g., AWS Secrets Manager, Azure Key Vault) configuration is backed up securely. **Do not commit `.env` to Git.**

## Restore Procedure

### Prerequisities
1.  Docker environment is running (`docker-compose up -d`).
2.  Backup file is available on the host.

### Database Restore
**Warning:** This operation overwrites the existing database.

```bash
cd /path/to/project
chmod +x scripts/restore_db.sh
./scripts/restore_db.sh backups/backup_arcore_syncbridge_YYYYMMDD_HHMMSS.sql.gz
```

### Full System Recovery (Clean Slate)
1.  Clone Repository.
2.  Restore `.env` file from secure storage.
3.  Start containers: `docker-compose up -d`.
4.  Run Database Restore using the latest backup.
5.  Restart Backend to ensure connection pools are fresh: `docker-compose restart backend`.

## Verification
After restore:
1.  Log in to the Admin UI.
2.  Verify "Sync Definitions" are visible.
3.  Check "Database Instances" status.
4.  Run a "Drift Report" on a critical definition to verify Ledger consistency.
