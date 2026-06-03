#!/usr/bin/env bash
# Archive the ByteBlaster audio storage volume to a host tgz file.
#
# Usage:
#   ./scripts/backup-sounds.sh                              # → backups/sounds-YYYYMMDD-HHMMSS.tgz
#   OUTFILE=my.tgz ./scripts/backup-sounds.sh               # custom output path
#   COMPOSE_FILE=docker-compose.yml ./scripts/backup-sounds.sh  # prod stack
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
SERVICE="${BACKEND_SERVICE:-backend}"
SOUND_DIR="${SOUND_DIR:-/data/sounds}"

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
OUTFILE="${OUTFILE:-backups/sounds-${TS}.tgz}"

echo "→ Archiving '$SOUND_DIR' from service '$SERVICE'"
echo "→ Output: $OUTFILE"

docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE" \
  tar -C "$SOUND_DIR" -czf - . \
  > "$OUTFILE"

COUNT=$(tar -tzf "$OUTFILE" | grep -cv '/$' || true)
SIZE=$(du -h "$OUTFILE" | cut -f1)
echo "✓ Archive written ($SIZE, $COUNT files)."
