from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Tag

MAX_TAGS_PER_SOUND = 10
TAG_NAME_RE = re.compile(r"^[a-z0-9_\- ]+$")


def normalize_tag_names(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in names:
        n = raw.strip().lower()
        if not n:
            continue
        if len(n) > 32 or not TAG_NAME_RE.match(n):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid tag name: {raw!r}. Allowed: 1-32 chars, [a-z0-9_- ].",
            )
        if n in seen:
            continue
        seen.add(n)
        out.append(n)
    if len(out) > MAX_TAGS_PER_SOUND:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Too many tags (max {MAX_TAGS_PER_SOUND}).",
        )
    return out


async def get_or_create_tags(session: AsyncSession, names: list[str]) -> list[Tag]:
    cleaned = normalize_tag_names(names)
    if not cleaned:
        return []
    existing = (
        await session.execute(select(Tag).where(Tag.name.in_(cleaned)))
    ).scalars().all()
    by_name = {t.name: t for t in existing}
    for n in cleaned:
        if n not in by_name:
            t = Tag(name=n)
            session.add(t)
            by_name[n] = t
    # Flush so new tags get ids before we attach them via the association.
    await session.flush()
    return [by_name[n] for n in cleaned]
