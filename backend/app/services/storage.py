from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from ..config import Settings

ALLOWED_MIME = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/wave": ".wav",
}

CHUNK = 1024 * 64


@dataclass
class StoredFile:
    path: Path
    mime: str
    size: int
    duration_ms: int | None = None


def probe_duration_ms(path: Path) -> int | None:
    try:
        from mutagen import File as MutagenFile
        m = MutagenFile(str(path))
        if m is None or m.info is None:
            return None
        secs = float(getattr(m.info, "length", 0.0) or 0.0)
        ms = int(round(secs * 1000))
        return ms if ms > 0 else None
    except Exception:
        return None


async def save_upload(upload: UploadFile, settings: Settings) -> StoredFile:
    mime = (upload.content_type or "").lower()
    if mime not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported mime type: {mime!r}. Allowed: mp3, wav.",
        )
    ext = ALLOWED_MIME[mime]

    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    hasher = hashlib.sha256()
    size = 0
    # First pass: read into a temp file under storage_dir so we don't double-buffer in memory.
    tmp = settings.storage_dir / f".incoming-{id(upload)}.part"
    try:
        with tmp.open("wb") as out:
            while chunk := await upload.read(CHUNK):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large (>{settings.max_upload_bytes} bytes).",
                    )
                hasher.update(chunk)
                out.write(chunk)
        digest = hasher.hexdigest()
        final = settings.storage_dir / f"{digest}{ext}"
        if final.exists():
            tmp.unlink(missing_ok=True)
        else:
            tmp.rename(final)
    except HTTPException:
        tmp.unlink(missing_ok=True)
        raise
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    return StoredFile(path=final, mime=mime, size=size, duration_ms=probe_duration_ms(final))


def resolve_path(file_path: str, settings: Settings) -> Path:
    p = Path(file_path).resolve()
    base = settings.storage_dir.resolve()
    # Defence-in-depth: ensure the stored path lives under storage_dir.
    if base not in p.parents and p != base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if not p.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return p
