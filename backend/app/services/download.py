from __future__ import annotations

import hashlib
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status

from ..config import Settings
from .storage import ALLOWED_MIME, CHUNK, StoredFile, probe_duration_ms


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must use http or https.",
        )
    if not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is missing a host.",
        )


async def download_url(url: str, settings: Settings) -> StoredFile:
    """Stream a remote mp3/wav into storage, mirroring save_upload's contract.

    Enforces size + mime in the same way uploads do so the rest of the
    upload pipeline doesn't need to know the difference.
    """
    _validate_url(url)
    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    timeout = httpx.Timeout(15.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            async with client.stream("GET", url) as resp:
                if resp.status_code >= 400:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Remote returned HTTP {resp.status_code}.",
                    )
                mime = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
                if mime not in ALLOWED_MIME:
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail=f"Unsupported mime type from URL: {mime!r}. Allowed: mp3, wav.",
                    )
                ext = ALLOWED_MIME[mime]

                # Reject early when the remote advertises an over-limit size.
                cl = resp.headers.get("content-length")
                if cl and cl.isdigit() and int(cl) > settings.max_upload_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Remote file too large (>{settings.max_upload_bytes} bytes).",
                    )

                hasher = hashlib.sha256()
                size = 0
                tmp = settings.storage_dir / f".incoming-url-{id(resp)}.part"
                try:
                    with tmp.open("wb") as out:
                        async for chunk in resp.aiter_bytes(CHUNK):
                            size += len(chunk)
                            if size > settings.max_upload_bytes:
                                raise HTTPException(
                                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                    detail=f"Remote file too large (>{settings.max_upload_bytes} bytes).",
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
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not fetch URL: {exc.__class__.__name__}.",
        ) from None

    return StoredFile(path=final, mime=mime, size=size, duration_ms=probe_duration_ms(final))


def derive_filename_from_url(url: str) -> str | None:
    """Pull the last path segment so we can store original_filename."""
    path = urlparse(url).path
    if not path:
        return None
    name = path.rsplit("/", 1)[-1]
    return name or None
