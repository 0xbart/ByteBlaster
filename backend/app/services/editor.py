from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import HTTPException, status

from ..config import Settings
from .download import _validate_url
from .storage import CHUNK, StoredFile, probe_duration_ms

MAX_CUT_SECONDS = 60.0


async def _fetch_to_tmp(source_url: str, settings: Settings) -> Path:
    _validate_url(source_url)
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    tmp = settings.storage_dir / f".editor-src-{uuid4().hex}.bin"
    timeout = httpx.Timeout(15.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            async with client.stream("GET", source_url) as resp:
                if resp.status_code >= 400:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Source returned HTTP {resp.status_code}.",
                    )
                size = 0
                with tmp.open("wb") as out:
                    async for chunk in resp.aiter_bytes(CHUNK):
                        size += len(chunk)
                        if size > settings.max_upload_bytes:
                            raise HTTPException(
                                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                detail="Source file too large.",
                            )
                        out.write(chunk)
    except HTTPException:
        tmp.unlink(missing_ok=True)
        raise
    except httpx.RequestError as exc:
        tmp.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not fetch source: {exc.__class__.__name__}.",
        ) from None
    return tmp


async def trim_to_storage(
    source: Path | str,
    start_s: float,
    end_s: float,
    settings: Settings,
) -> StoredFile:
    """ffmpeg-cut a source file and persist it.

    `source` may be a local Path (read directly) or an http(s) URL that
    will be fetched first.
    """
    if end_s <= start_s:
        raise HTTPException(
            status_code=422, detail="end_s must be greater than start_s."
        )
    if end_s - start_s > MAX_CUT_SECONDS:
        raise HTTPException(
            status_code=422,
            detail=f"Cut length must be <= {MAX_CUT_SECONDS:.0f}s.",
        )

    fetched_tmp: Path | None = None
    if isinstance(source, Path):
        tmp_in = source
    else:
        fetched_tmp = await _fetch_to_tmp(source, settings)
        tmp_in = fetched_tmp
    in_duration_ms = probe_duration_ms(tmp_in)
    if in_duration_ms is not None and (end_s * 1000) > in_duration_ms + 50:
        if fetched_tmp is not None:
            fetched_tmp.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail=f"end_s ({end_s:.2f}s) exceeds source duration "
            f"({in_duration_ms / 1000:.2f}s).",
        )

    tmp_out = settings.storage_dir / f".editor-cut-{uuid4().hex}.mp3"
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{start_s:.3f}",
            "-to",
            f"{end_s:.3f}",
            "-i",
            str(tmp_in),
            "-c:a",
            "libmp3lame",
            "-q:a",
            "4",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-y",
            str(tmp_out),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ffmpeg failed: {stderr.decode(errors='ignore')[:200]}",
            )
    finally:
        if fetched_tmp is not None:
            fetched_tmp.unlink(missing_ok=True)

    if not tmp_out.is_file() or tmp_out.stat().st_size == 0:
        tmp_out.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ffmpeg produced no output.",
        )

    size = tmp_out.stat().st_size
    if size > settings.max_upload_bytes:
        tmp_out.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Trimmed file exceeds upload limit.",
        )

    # Hash + move to final hashed name to dedup identical re-cuts.
    hasher = hashlib.sha256()
    with tmp_out.open("rb") as f:
        while chunk := f.read(CHUNK):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    final = settings.storage_dir / f"{digest}.mp3"
    if final.exists():
        tmp_out.unlink(missing_ok=True)
    else:
        tmp_out.rename(final)

    duration_ms = probe_duration_ms(final)
    return StoredFile(
        path=final, mime="audio/mpeg", size=size, duration_ms=duration_ms
    )
