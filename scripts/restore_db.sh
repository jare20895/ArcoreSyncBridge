#!/bin/bash
set -e

# Usage: ./restore_db.sh <backup_file.sql.gz>

BACKUP_FILE="$1"
CONTAINER_NAME="arcoresyncbridge-db-1"
DB_USER="arcore"
DB_NAME="arcore_syncbridge"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found."
    exit 1
fi

echo "WARNING: This will overwrite the database '${DB_NAME}' in container '${CONTAINER_NAME}'."
echo "Press Ctrl+C to cancel or Enter to continue..."
read

echo "Restoring from ${BACKUP_FILE}..."

# Drop and recreate DB to ensure clean state (requires active connections to be killed)
# For simplicity, we assume we can just psql -f. But if tables exist, it might error or append.
# Best practice: Drop/Create.
# We need to connect to 'postgres' db to drop target db.

echo "Terminating existing connections..."
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();"

echo "Dropping database..."
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"

echo "Recreating database..."
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE ${DB_NAME};"

echo "Applying backup..."
zcat "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"

echo "Restore completed successfully."
