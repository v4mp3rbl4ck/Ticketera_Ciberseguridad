#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Uso: ./scripts/restore.sh ./backups/ticketera-backup-YYYYMMDD-HHMMSS.tar.gz"
  exit 1
fi

ARCHIVE="$1"
WORKDIR="./backups/restore-$(date +%Y%m%d-%H%M%S)"
POSTGRES_DB="${POSTGRES_DB:-ticketera}"
POSTGRES_USER="${POSTGRES_USER:-ticketera}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-ticketera-postgres}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-ticketera-backend}"

mkdir -p "$WORKDIR"
tar -xzf "$ARCHIVE" -C "$WORKDIR"

printf '[restore] Restaurando base de datos...
'
docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$WORKDIR/database.sql"

if [ -d "$WORKDIR/uploads" ]; then
  printf '[restore] Restaurando evidencias...
'
  docker cp "$WORKDIR/uploads/." "$BACKEND_CONTAINER:/app/uploads/"
fi

rm -rf "$WORKDIR"
printf '[restore] OK
'
