#!/usr/bin/env bash
# Restore a ByteBlaster Postgres dump (custom format, produced by backup-db.sh).
#
# Usage:
#   ./scripts/restore-db.sh backups/byteblaster-YYYYMMDD-HHMMSS.dump
#   COMPOSE_FILE=docker-compose.yml ./scripts/restore-db.sh path/to/file.dump
#
# DESTRUCTIVE: existing tables/data in the target database will be dropped via
# pg_restore --clean --if-exists. Stop the backend first to avoid live writes:
#   docker compose -f <compose> stop backend
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 <dump-file>" >&2
  exit 2
fi

DUMP_FILE="$1"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
SERVICE="${DB_SERVICE:-db}"
DB_USER="${DB_USER:-byteblaster}"
DB_NAME="${DB_NAME:-byteblaster}"

cd "$(dirname "$0")/.."

if [ ! -f "$DUMP_FILE" ]; then
  echo "ERROR: dump file not found: $DUMP_FILE" >&2
  exit 1
fi
if [ ! -f "$COMPOSE_FILE" ]; then
  echo "ERROR: compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi
if ! docker compose -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -qx "$SERVICE"; then
  echo "ERROR: '$SERVICE' is not running in $COMPOSE_FILE" >&2
  echo "Start it first: docker compose -f $COMPOSE_FILE up -d $SERVICE" >&2
  exit 1
fi

echo "⚠  About to restore '$DUMP_FILE' into database '$DB_NAME' (user '$DB_USER')."
echo "    This DROPS existing tables before recreating them."
read -rp "Continue? [y/N] " ans
case "$ans" in
  y|Y|yes|YES) ;;
  *) echo "Aborted."; exit 1 ;;
esac

# Kill active sessions so DROP/CREATE doesn't deadlock against the backend.
docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE" \
  psql -U "$DB_USER" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DB_NAME' AND pid <> pg_backend_pid();" \
  >/dev/null

echo "→ Restoring…"
docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE" \
  pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner --no-privileges \
  < "$DUMP_FILE"

echo "✓ Restore complete."
echo "  Restart backend so SQLAlchemy reconnects cleanly:"
echo "    docker compose -f $COMPOSE_FILE restart backend"
