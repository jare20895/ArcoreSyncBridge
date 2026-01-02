#!/bin/bash
set -e

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="arcoresyncbridge-db-1"
DB_USER="arcore"
DB_NAME="arcore_syncbridge"
FILENAME="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"

# Ensure backup dir exists
mkdir -p "$BACKUP_DIR"

echo "Starting backup of ${DB_NAME} from container ${CONTAINER_NAME}..."

# Execute pg_dump inside container and pipe to gzip
docker exec -t "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$FILENAME"

echo "Backup completed successfully: ${FILENAME}"
ls -lh "$FILENAME"
