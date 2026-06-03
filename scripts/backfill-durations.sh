#!/usr/bin/env bash
# Backfill sounds.duration_ms for rows where it is NULL.
# Reads each file from /data/sounds via mutagen inside the backend container.
#
# Usage:
#   ./scripts/backfill-durations.sh
#   COMPOSE_FILE=docker-compose.yml ./scripts/backfill-durations.sh
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
SERVICE="${BACKEND_SERVICE:-backend}"

cd "$(dirname "$0")/.."

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "ERROR: compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi
if ! docker compose -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -qx "$SERVICE"; then
  echo "ERROR: '$SERVICE' is not running in $COMPOSE_FILE" >&2
  exit 1
fi

docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE" python - <<'PY'
import asyncio
from mutagen import File as MutagenFile
from sqlalchemy import select
from app.db import SessionLocal
from app.models import Sound


async def main() -> None:
    updated = 0
    skipped = 0
    async with SessionLocal() as session:
        rows = (
            await session.execute(
                select(Sound).where(Sound.duration_ms.is_(None))
            )
        ).scalars().all()
        for snd in rows:
            try:
                m = MutagenFile(snd.file_path)
                if m is not None and m.info is not None:
                    secs = float(getattr(m.info, "length", 0.0) or 0.0)
                    ms = int(round(secs * 1000))
                    if ms > 0:
                        snd.duration_ms = ms
                        updated += 1
                        continue
            except Exception as exc:
                print(f"  ! sound id={snd.id} failed: {exc.__class__.__name__}")
            skipped += 1
        await session.commit()
    print(f"Updated {updated} sounds (skipped {skipped}, total scanned {updated + skipped}).")


asyncio.run(main())
PY
