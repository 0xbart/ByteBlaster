from __future__ import annotations

import asyncio
import re
import secrets
import time
from pathlib import Path
from typing import Annotated, Any

from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..deps import CurrentUser, DbSession, SettingsDep
from ..models import Category, Sound
from ..schemas import (
    ExploreResult,
    ExploreSearchOut,
    LocalCategory,
    LocalImportIn,
    LocalSound,
    LocalSoundsOut,
    SoundOut,
    WsSoundAddedEvent,
    YoutubeFetchIn,
    YoutubeFetchOut,
)
from ..services import storage
from ..services.tags import get_or_create_tags
from ..ws.manager import manager

router = APIRouter(prefix="/explore", tags=["explore"])

_BASE = "https://www.myinstants.com"
_SEARCH_URL = f"{_BASE}/en/search/"
_UA = "Mozilla/5.0"
_TTL_SECONDS = 60.0
_PLAY_RE = re.compile(r"play\(\s*['\"]([^'\"]+\.mp3)['\"]")
_TITLE_PAGE_RE = re.compile(r"Page\s+\d+\s+of\s+(\d+)", re.IGNORECASE)
_cache: dict[tuple[str, int], tuple[ExploreSearchOut, float]] = {}


def _parse_results(html: str, query: str, page: int) -> ExploreSearchOut:
    soup = BeautifulSoup(html, "lxml")
    results: list[ExploreResult] = []
    seen: set[str] = set()

    containers = soup.select(".instant")
    for c in containers:
        mp3_path: str | None = None
        for btn in c.find_all(["button", "div"]):
            onclick = btn.get("onclick") or ""
            m = _PLAY_RE.search(onclick)
            if m:
                mp3_path = m.group(1)
                break
        if not mp3_path:
            scripts = c.find_all(attrs={"onmousedown": True}) + c.find_all(attrs={"onclick": True})
            for el in scripts:
                attr = (el.get("onmousedown") or "") + " " + (el.get("onclick") or "")
                m = _PLAY_RE.search(attr)
                if m:
                    mp3_path = m.group(1)
                    break
        if not mp3_path:
            continue

        title_el = c.select_one("a.instant-link") or c.select_one("a.link-secondary") or c.find("a")
        title = (title_el.get_text(strip=True) if title_el else "").strip()
        if not title:
            button = c.find("button")
            title = (button.get("title", "").strip() if button else "") or mp3_path.rsplit("/", 1)[-1]
        if not title:
            continue

        absolute = mp3_path if mp3_path.startswith("http") else f"{_BASE}{mp3_path}"
        if absolute in seen:
            continue
        seen.add(absolute)
        results.append(ExploreResult(title=title, mp3_url=absolute))

    has_more = False

    title_tag = soup.find("title")
    if title_tag:
        m = _TITLE_PAGE_RE.search(title_tag.get_text())
        if m:
            total_pages = int(m.group(1))
            has_more = page < total_pages

    if not has_more:
        next_link = soup.select_one('a[rel="next"]')
        if next_link is not None:
            has_more = True
        else:
            # Fallback: search for pagination anchor containing page={page+1}
            for a in soup.select("a"):
                href = a.get("href", "")
                if f"page={page + 1}" in href:
                    has_more = True
                    break

            if page == 1 and len(results) == 36:
                # page X of X not found on page=1, assume that there might be more
                has_more = True

    return ExploreSearchOut(query=query, page=page, results=results, has_more=has_more)


def _cache_get(key: tuple[str, int]) -> ExploreSearchOut | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    out, expires = entry
    if expires < time.monotonic():
        _cache.pop(key, None)
        return None
    return out


def _cache_set(key: tuple[str, int], out: ExploreSearchOut) -> None:
    if len(_cache) >= 200:
        # Drop arbitrary entry to keep size bounded.
        _cache.pop(next(iter(_cache)))
    _cache[key] = (out, time.monotonic() + _TTL_SECONDS)


@router.get("/search", response_model=ExploreSearchOut)
async def search_explore(
    _: CurrentUser,
    q: Annotated[str, Query(min_length=1, max_length=64)],
    page: Annotated[int, Query(ge=1, le=50)] = 1,
) -> ExploreSearchOut:
    q_clean = q.strip()
    if not q_clean:
        raise HTTPException(status_code=422, detail="Query must not be empty.")

    key = (q_clean.lower(), page)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    try:
        async with httpx.AsyncClient(
            timeout=8.0, headers={"User-Agent": _UA, "Accept-Language": "en"}
        ) as client:
            resp = await client.get(_SEARCH_URL, params={"name": q_clean, "page": page})
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Myinstants timed out.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Myinstants request failed: {exc.__class__.__name__}",
        ) from exc

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Myinstants returned HTTP {resp.status_code}.",
        )

    out = _parse_results(resp.text, q_clean, page)
    _cache_set(key, out)
    return out


# ---------------------------------------------------------------------------
# Same-origin proxy for myinstants mp3s. The browser audio editor (wavesurfer)
# fetch()es the file to draw a waveform, which CORS blocks on the myinstants
# CDN. We stream it through here so it's same-origin. SSRF-guarded to the
# myinstants host only; trim itself still fetches the real URL server-side.
# ---------------------------------------------------------------------------


def _is_myinstants_mp3(url: str) -> bool:
    from urllib.parse import urlparse

    try:
        p = urlparse(url)
    except ValueError:
        return False
    host = (p.hostname or "").lower()
    return (
        p.scheme == "https"
        and (host == "myinstants.com" or host.endswith(".myinstants.com"))
        and p.path.lower().endswith(".mp3")
    )


@router.get("/proxy")
async def proxy_mp3(
    _: CurrentUser,
    url: Annotated[str, Query(min_length=8, max_length=512)],
) -> StreamingResponse:
    if not _is_myinstants_mp3(url):
        raise HTTPException(status_code=400, detail="Only myinstants mp3 URLs are allowed.")

    client = httpx.AsyncClient(timeout=15.0, headers={"User-Agent": _UA})
    try:
        req = client.build_request("GET", url)
        upstream = await client.send(req, stream=True)
    except httpx.HTTPError as exc:
        await client.aclose()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fetch failed: {exc.__class__.__name__}",
        ) from exc

    if upstream.status_code != 200:
        await upstream.aclose()
        await client.aclose()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream returned HTTP {upstream.status_code}.",
        )

    async def _stream() -> Any:
        try:
            async for chunk in upstream.aiter_bytes():
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(_stream(), media_type="audio/mpeg")


# ---------------------------------------------------------------------------
# YouTube → mp3 via yt-dlp (max 90 s, served from temp preview directory)
# ---------------------------------------------------------------------------

# Hard ceiling: videos longer than this are rejected before download.
MAX_YT_DURATION_S = 900  # 15 min
# Videos longer than this may only be sent to the editor, not saved directly
# (enforced server-side in routers/sounds.py on the preview-ingest path).
MAX_YT_DIRECT_DURATION_S = 90
_PREVIEW_SUBDIR = "_yt_previews"
_PREVIEW_TTL_SECONDS = 3600.0
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_\-]{8,40}\.mp3$")


def _yt_probe_sync(url: str) -> dict[str, Any]:
    from yt_dlp import YoutubeDL

    opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
        "noplaylist": True,
        "extract_flat": False,
        "socket_timeout": 10,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False) or {}
    # When yt-dlp falls back to a playlist (despite noplaylist) it returns
    # `_type=playlist` with entries; pick the first entry's metadata.
    if info.get("_type") == "playlist":
        entries = info.get("entries") or []
        if entries:
            return entries[0] or {}
        return {}
    return info


def _yt_download_sync(url: str, out_template: str) -> str:
    from yt_dlp import YoutubeDL

    opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ],
        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 15,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    # yt-dlp returns the post-postprocessing file via `requested_downloads`
    # (preferred) or `filepath`; fall back to swapping the extension.
    if info:
        downloads = info.get("requested_downloads") or []
        if downloads:
            filepath = downloads[0].get("filepath")
            if filepath:
                return filepath
        filepath = info.get("filepath")
        if filepath:
            return filepath
    return out_template.replace("%(ext)s", "mp3")


def _cleanup_old_previews(prev_dir: Path) -> None:
    cutoff = time.time() - _PREVIEW_TTL_SECONDS
    for f in prev_dir.iterdir():
        try:
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
        except OSError:
            continue


@router.post("/youtube/fetch", response_model=YoutubeFetchOut)
async def youtube_fetch(
    body: YoutubeFetchIn,
    _: CurrentUser,
    settings: SettingsDep,
) -> YoutubeFetchOut:
    url = body.url.strip()
    if not url:
        raise HTTPException(status_code=422, detail="URL must not be empty.")

    try:
        info = await asyncio.wait_for(asyncio.to_thread(_yt_probe_sync, url), timeout=20.0)
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="YouTube probe timed out.",
        ) from exc
    except Exception as exc:  # noqa: BLE001 — yt-dlp raises a hierarchy of errors
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"YouTube probe failed: {exc.__class__.__name__}",
        ) from exc

    duration_s = float(info.get("duration") or 0)
    if duration_s <= 0:
        raise HTTPException(status_code=422, detail="Could not determine duration.")
    if duration_s > MAX_YT_DURATION_S:
        raise HTTPException(
            status_code=422,
            detail=f"Audio is {duration_s:.1f}s; max is {MAX_YT_DURATION_S}s.",
        )

    title = (info.get("title") or "YouTube audio").strip() or "YouTube audio"

    prev_dir = settings.storage_dir / _PREVIEW_SUBDIR
    prev_dir.mkdir(parents=True, exist_ok=True)
    _cleanup_old_previews(prev_dir)

    token = secrets.token_urlsafe(12)
    out_path = prev_dir / f"{token}.mp3"
    out_template = str(prev_dir / f"{token}.%(ext)s")

    try:
        produced = await asyncio.wait_for(
            asyncio.to_thread(_yt_download_sync, url, out_template),
            timeout=60.0,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="YouTube download timed out.",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"YouTube download failed: {exc.__class__.__name__}",
        ) from exc

    produced_path = Path(produced)
    if produced_path != out_path:
        if produced_path.is_file():
            produced_path.rename(out_path)

    if not out_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="yt-dlp did not produce an mp3 file.",
        )

    # No size reject here: long previews (up to 15 min) may exceed the upload
    # limit but are temp files (1 h TTL) only saveable via the editor, which
    # re-checks the trimmed output size.
    return YoutubeFetchOut(
        title=title,
        duration_ms=int(round(duration_s * 1000)),
        preview_url=f"/api/explore/youtube/preview/{token}.mp3",
        editor_only=duration_s > MAX_YT_DIRECT_DURATION_S,
    )


@router.get("/youtube/preview/{token}")
async def youtube_preview(token: str, settings: SettingsDep) -> FileResponse:
    if not _TOKEN_RE.fullmatch(token):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    path = settings.storage_dir / _PREVIEW_SUBDIR / token
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return FileResponse(path, media_type="audio/mpeg", filename=token)


# ---------------------------------------------------------------------------
# Local library: browse/search mp3s dropped into the host `./sounds` folder
# (bind-mounted read-only at settings.local_sounds_dir). Top-level subfolders
# are categories; files in the root are grouped as "Uncategorized".
# ---------------------------------------------------------------------------

_UNCATEGORIZED = "Uncategorized"
# Probing duration with mutagen is cheap per file but adds up across a big tree;
# cache by (path, mtime, size) so repeat list calls don't re-probe.
_duration_cache: dict[tuple[str, float, int], int | None] = {}


def _cached_duration(path: Path) -> int | None:
    try:
        st = path.stat()
    except OSError:
        return None
    key = (str(path), st.st_mtime, st.st_size)
    if key in _duration_cache:
        return _duration_cache[key]
    ms = storage.probe_duration_ms(path)
    if len(_duration_cache) >= 2000:
        _duration_cache.clear()
    _duration_cache[key] = ms
    return ms


@router.get("/local", response_model=LocalSoundsOut)
async def list_local(
    _: CurrentUser,
    settings: SettingsDep,
    q: Annotated[str | None, Query(max_length=64)] = None,
) -> LocalSoundsOut:
    base = settings.local_sounds_dir
    if not base.is_dir():
        return LocalSoundsOut(categories=[])

    needle = (q or "").strip().lower()
    buckets: dict[str, list[LocalSound]] = {}
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in storage.LOCAL_EXT_MIME:
            continue
        rel = path.relative_to(base)
        title = path.stem
        if needle and needle not in title.lower():
            continue
        category = " - ".join(rel.parts[:-1]) if len(rel.parts) > 1 else _UNCATEGORIZED
        rel_posix = rel.as_posix()
        buckets.setdefault(category, []).append(
            LocalSound(
                title=title,
                rel=rel_posix,
                url=f"/api/explore/local/file?rel={quote(rel_posix)}",
                duration_ms=_cached_duration(path),
            )
        )

    def _cat_sort_key(name: str) -> tuple[int, str]:
        # Uncategorized sinks to the bottom; everything else alphabetical.
        return (1, "") if name == _UNCATEGORIZED else (0, name.lower())

    categories = [
        LocalCategory(name=name, sounds=sorted(sounds, key=lambda s: s.title.lower()))
        for name, sounds in sorted(buckets.items(), key=lambda kv: _cat_sort_key(kv[0]))
    ]
    return LocalSoundsOut(categories=categories)


@router.get("/local/file")
async def get_local_file(
    _: CurrentUser,
    settings: SettingsDep,
    rel: Annotated[str, Query(min_length=1, max_length=1024)],
) -> FileResponse:
    path = storage.resolve_local_path(rel, settings)
    return FileResponse(
        path,
        media_type=storage.LOCAL_EXT_MIME[path.suffix.lower()],
        filename=path.name,
    )


@router.post("/local/import", response_model=SoundOut, status_code=status.HTTP_201_CREATED)
async def import_local(
    body: LocalImportIn,
    user: CurrentUser,
    session: DbSession,
    settings: SettingsDep,
) -> SoundOut:
    if body.category_id is not None:
        if (await session.get(Category, body.category_id)) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown category_id {body.category_id}.",
            )

    tag_objs = await get_or_create_tags(session, body.tags)

    src = storage.resolve_local_path(body.rel, settings)
    stored = storage.store_local_copy(src, settings)

    sound = Sound(
        display_name=body.display_name.strip(),
        original_filename=src.name,
        file_path=str(stored.path),
        mime_type=stored.mime,
        size_bytes=stored.size,
        uploaded_by_user_id=user.id,
        category_id=body.category_id,
        duration_ms=stored.duration_ms,
    )
    sound.tags = tag_objs
    session.add(sound)
    await session.commit()

    result = await session.execute(
        select(Sound)
        .options(
            selectinload(Sound.uploader),
            selectinload(Sound.category),
            selectinload(Sound.tags),
        )
        .where(Sound.id == sound.id)
    )
    full = result.scalar_one()
    out = SoundOut(
        id=full.id,
        display_name=full.display_name,
        mime_type=full.mime_type,
        size_bytes=full.size_bytes,
        uploaded_by_user_id=full.uploaded_by_user_id,
        uploader_username=full.uploader.username,
        category_id=full.category_id,
        category_name=full.category.name if full.category else None,
        tags=sorted(t.name for t in full.tags),
        created_at=full.created_at,
        url=f"/api/sounds/{full.id}/file",
        is_favorite=False,
        duration_ms=full.duration_ms,
    )
    await manager.broadcast(WsSoundAddedEvent(sound=out, by=user.username))
    return out
