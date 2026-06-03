#!/usr/bin/env bash
# Dump the ByteBlaster Postgres database to a host file.
#
# Usage:
#   ./scripts/backup-db.sh                              # → backups/byteblaster-YYYYMMDD-HHMMSS.dump
#   OUTFILE=my.dump ./scripts/backup-db.sh              # custom output path
#   COMPOSE_FILE=docker-compose.yml ./scripts/backup-db.sh  # prod stack
#
# Uses pg_dump custom format (-Fc) — restore via scripts/restore-db.sh.
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
SERVICE="${DB_SERVICE:-db}"
DB_USER="${DB_USER:-byteblaster}"
DB_NAME="${DB_NAME:-byteblaster}"

cd "$(dirname "$0")/.."

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "ERROR: compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

if ! docker compose -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -qx "$SERVICE"; then
  echo "ERROR: '$SERVICE' is not running in $COMPOSE_FILE" >&2
  echo "Start it first: docker compose -f $COMPOSE_FILE up -d $SERVICE" >&2
  exit 1
fi

mkdir -p backups
TS=$(date +%Y%m%d-%H%M%S)
OUTFILE="${OUTFILE:-backups/byteblaster-${TS}.dump}"

echo "→ Dumping database '$DB_NAME' as user '$DB_USER' from service '$SERVICE'"
echo "→ Output: $OUTFILE"

docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE" \
  pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc --no-owner --no-privileges \
  > "$OUTFILE"

SIZE=$(du -h "$OUTFILE" | cut -f1)
echo "✓ Backup written ($SIZE)."
