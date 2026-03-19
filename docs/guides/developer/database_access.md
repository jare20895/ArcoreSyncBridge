# Database Access Guide

## Overview
The Arcore SyncBridge database is hosted in a Docker container (`arcoresyncbridge-db-1`) running PostgreSQL 15. It is accessible from the host machine via a mapped port.

## Connection Details

### Admin Tools (DBeaver, pgAdmin, DataGrip)
To connect using a desktop client:

- **Host:** `localhost`
- **Port:** `5465`
- **Database:** `arcore_syncbridge`
- **Username:** value from `backend/.env`
- **Password:** value from `backend/.env`
- **Driver:** PostgreSQL

### CLI Access
To connect via `psql` from your terminal (requires `psql` installed):
```bash
psql -h localhost -p 5465 -U "$POSTGRES_USER" -d arcore_syncbridge
```

To connect directly inside the container:
```bash
docker exec -it arcoresyncbridge-db-1 psql -U arcore -d arcore_syncbridge
```

## SQLAdmin
A web-based admin interface is available at:
`http://localhost:8401/admin`
