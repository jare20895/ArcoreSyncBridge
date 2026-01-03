# CDC Setup Guide

## Prerequisites
1.  **PostgreSQL Configuration:**
    The database must be configured with `wal_level = logical` to support logical replication.
    
    If using Docker Compose, ensure the `db` service has the command:
    ```yaml
    command: postgres -c wal_level=logical
    ```
    
    You must **restart the database container** for this change to take effect:
    ```bash
    docker-compose down db
    docker-compose up -d db
    ```

2.  **Dependencies:**
    Ensure `psycopg2-binary` is installed in the backend environment.

3.  **Permissions:**
    The database user (`arcore`) must have `REPLICATION` privilege.
    Usually the default superuser (or user created by init script) has this.
    If not: `ALTER USER arcore WITH REPLICATION;`

## Running the CDC Worker
Run the worker via the script, passing the Database Instance ID:

```bash
docker exec -it arcoresyncbridge-backend-1 python scripts/run_cdc.py <INSTANCE_UUID>
```

Or run without arguments to auto-discover the primary active instance.

## Verification
Check logs for "Starting replication from LSN ...".
Check Redis stream `arcore:cdc:events`.
