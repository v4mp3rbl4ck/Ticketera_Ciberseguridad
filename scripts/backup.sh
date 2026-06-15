#!/usr/bin/env bash
set -euo pipefail

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_DIR:-./backups/$STAMP}"
mkdir -p "$BACKUP_DIR"

POSTGRES_DB="${POSTGRES_DB:-ticketera}"
POSTGRES_USER="${POSTGRES_USER:-ticketera}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-ticketera-postgres}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-ticketera-backend}"

printf '[backup] Generando dump PostgreSQL...
'
docker exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_DIR/database.sql"

printf '[backup] Copiando evidencias...
'
docker cp "$BACKEND_CONTAINER:/app/uploads" "$BACKUP_DIR/uploads"

printf '[backup] Comprimiendo...
'
tar -czf "./backups/ticketera-backup-$STAMP.tar.gz" -C "$BACKUP_DIR" .
rm -rf "$BACKUP_DIR"
printf '[backup] OK: ./backups/ticketera-backup-%s.tar.gz
' "$STAMP"
