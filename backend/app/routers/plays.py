from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..config import Settings, get_settings
from ..deps import CurrentUser, DbSession
from ..models import Play, Sound, User
from ..schemas import PlayOut, WsPlayEvent
from ..ws.manager import manager


# In-memory sliding window: user_id -> deque of recent play timestamps.
# Single-process only; fine for office-scale.
_recent: dict[int, deque[float]] = defaultdict(deque)


def _check_rate_limit(user: User, settings: Settings) -> None:
    if user.is_superadmin or settings.rate_limit_plays <= 0:
        return
    window = settings.rate_limit_window_seconds
    now = time.monotonic()
    cutoff = now - window
    bucket = _recent[user.id]
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_plays:
        retry_in = max(0, int(window - (now - bucket[0]) + 1))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit: max {settings.rate_limit_plays} plays per {window}s. Try again in {retry_in}s.",
            headers={"Retry-After": str(retry_in)},
        )
    bucket.append(now)

router = APIRouter(tags=["plays"])


def _to_out(play: Play) -> PlayOut:
    return PlayOut(
        id=play.id,
        sound_id=play.sound_id,
        sound_display_name=play.sound.display_name,
        played_by_user_id=play.played_by_user_id,
        played_by_username=play.user.username,
        played_at=play.played_at,
    )


@router.post("/sounds/{sound_id}/play", response_model=PlayOut, status_code=status.HTTP_201_CREATED)
async def play_sound(
    sound_id: int,
    user: CurrentUser,
    session: DbSession,
    settings: Settings = Depends(get_settings),
) -> PlayOut:
    _check_rate_limit(user, settings)
    sound = await session.get(Sound, sound_id)
    if sound is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    play = Play(sound_id=sound_id, played_by_user_id=user.id)
    session.add(play)
    await session.commit()
    await session.refresh(play, attribute_names=["sound", "user"])

    out = _to_out(play)
    await manager.broadcast(
        WsPlayEvent(
            sound_id=sound.id,
            sound_url=f"/api/sounds/{sound.id}/file",
            display_name=sound.display_name,
            by=user.username,
            at=play.played_at,
        )
    )
    return out


@router.get("/plays", response_model=list[PlayOut])
async def list_plays(
    _: CurrentUser,
    session: DbSession,
    limit: int = Query(50, ge=1, le=500),
) -> list[PlayOut]:
    result = await session.execute(
        select(Play)
        .options(selectinload(Play.sound), selectinload(Play.user))
        .order_by(Play.played_at.desc())
        .limit(limit)
    )
    return [_to_out(p) for p in result.scalars().all()]
