from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import desc, func, select

from ..deps import CurrentUser, DbSession
from ..models import Category, Play, Sound, User
from ..schemas import SoundStatOut, UserStatOut

router = APIRouter(tags=["stats"])


@router.get("/stats/sounds", response_model=list[SoundStatOut])
async def stats_all_sounds(_: CurrentUser, session: DbSession) -> list[SoundStatOut]:
    stmt = (
        select(
            Sound.id,
            Sound.display_name,
            Category.name,
            func.count(Play.id).label("play_count"),
        )
        .select_from(Sound)
        .outerjoin(Play, Play.sound_id == Sound.id)
        .outerjoin(Category, Category.id == Sound.category_id)
        .group_by(Sound.id, Category.name)
        .order_by(desc("play_count"), Sound.display_name)
    )
    result = await session.execute(stmt)
    return [
        SoundStatOut(
            sound_id=row[0],
            display_name=row[1],
            category_name=row[2],
            play_count=row[3],
        )
        for row in result.all()
    ]


@router.get("/stats/users", response_model=list[UserStatOut])
async def stats_active_users(
    _: CurrentUser,
    session: DbSession,
    limit: int = Query(20, ge=1, le=100),
) -> list[UserStatOut]:
    stmt = (
        select(
            User.id,
            User.username,
            func.count(Play.id).label("play_count"),
        )
        .select_from(User)
        .join(Play, Play.played_by_user_id == User.id)
        .group_by(User.id)
        .order_by(desc("play_count"), User.username)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [
        UserStatOut(user_id=row[0], username=row[1], play_count=row[2])
        for row in result.all()
    ]


@router.get("/stats/trending", response_model=list[SoundStatOut])
async def stats_trending(
    _: CurrentUser,
    session: DbSession,
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=100),
) -> list[SoundStatOut]:
    since = datetime.now(tz=UTC) - timedelta(days=days)
    stmt = (
        select(
            Sound.id,
            Sound.display_name,
            Category.name,
            func.count(Play.id).label("play_count"),
        )
        .select_from(Sound)
        .join(Play, Play.sound_id == Sound.id)
        .outerjoin(Category, Category.id == Sound.category_id)
        .where(Play.played_at >= since)
        .group_by(Sound.id, Category.name)
        .order_by(desc("play_count"), Sound.display_name)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [
        SoundStatOut(
            sound_id=row[0],
            display_name=row[1],
            category_name=row[2],
            play_count=row[3],
        )
        for row in result.all()
    ]
