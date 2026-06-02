from __future__ import annotations

import re
import time
from typing import Annotated

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Query, status

from ..deps import CurrentUser
from ..schemas import ExploreResult, ExploreSearchOut

router = APIRouter(prefix="/explore", tags=["explore"])

_BASE = "https://www.myinstants.com"
_SEARCH_URL = f"{_BASE}/en/search/"
_UA = "Mozilla/5.0 (compatible; ByteBlaster/1.0)"
_TTL_SECONDS = 60.0
_PLAY_RE = re.compile(r"play\(\s*['\"]([^'\"]+\.mp3)['\"]")
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
