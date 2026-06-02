from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum

from fastapi import APIRouter, Query
from sqlalchemy import desc, func, select

from ..deps import CurrentUser, DbSession
from ..models import Category, Play, Sound, User
from ..schemas import CategoryStatOut, OverviewStatOut, SoundStatOut, UserStatOut

router = APIRouter(tags=["stats"])


class Window(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    all = "all"


_WINDOW_DAYS: dict[Window, int | None] = {
    Window.day: 1,
    Window.week: 7,
    Window.month: 30,
    Window.all: None,
}


def _since(window: Window) -> datetime | None:
    days = _WINDOW_DAYS[window]
    return None if days is None else datetime.now(tz=UTC) - timedelta(days=days)


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


@router.get("/stats/overview", response_model=OverviewStatOut)
async def stats_overview(_: CurrentUser, session: DbSession) -> OverviewStatOut:
    now = datetime.now(tz=UTC)
    total_sounds = (await session.execute(select(func.count(Sound.id)))).scalar_one()
    total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
    total_plays = (await session.execute(select(func.count(Play.id)))).scalar_one()
    plays_day = (
        await session.execute(
            select(func.count(Play.id)).where(Play.played_at >= now - timedelta(days=1))
        )
    ).scalar_one()
    plays_week = (
        await session.execute(
            select(func.count(Play.id)).where(Play.played_at >= now - timedelta(days=7))
        )
    ).scalar_one()
    plays_month = (
        await session.execute(
            select(func.count(Play.id)).where(Play.played_at >= now - timedelta(days=30))
        )
    ).scalar_one()
    return OverviewStatOut(
        total_sounds=total_sounds,
        total_users=total_users,
        total_plays=total_plays,
        plays_day=plays_day,
        plays_week=plays_week,
        plays_month=plays_month,
    )


@router.get("/stats/sounds/top", response_model=list[SoundStatOut])
async def stats_top_sounds(
    _: CurrentUser,
    session: DbSession,
    window: Window = Window.week,
    limit: int = Query(10, ge=1, le=100),
) -> list[SoundStatOut]:
    since = _since(window)
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
        .group_by(Sound.id, Category.name)
        .order_by(desc("play_count"), Sound.display_name)
        .limit(limit)
    )
    if since is not None:
        stmt = stmt.where(Play.played_at >= since)
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


@router.get("/stats/users/top", response_model=list[UserStatOut])
async def stats_top_users(
    _: CurrentUser,
    session: DbSession,
    window: Window = Window.week,
    limit: int = Query(20, ge=1, le=100),
) -> list[UserStatOut]:
    since = _since(window)
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
    if since is not None:
        stmt = stmt.where(Play.played_at >= since)
    result = await session.execute(stmt)
    return [
        UserStatOut(user_id=row[0], username=row[1], play_count=row[2])
        for row in result.all()
    ]


@router.get("/stats/categories", response_model=list[CategoryStatOut])
async def stats_categories(
    _: CurrentUser,
    session: DbSession,
    window: Window = Window.week,
) -> list[CategoryStatOut]:
    since = _since(window)
    stmt = (
        select(
            Sound.category_id,
            Category.name,
            func.count(Play.id).label("play_count"),
        )
        .select_from(Play)
        .join(Sound, Sound.id == Play.sound_id)
        .outerjoin(Category, Category.id == Sound.category_id)
        .group_by(Sound.category_id, Category.name)
        .order_by(desc("play_count"))
    )
    if since is not None:
        stmt = stmt.where(Play.played_at >= since)
    result = await session.execute(stmt)
    return [
        CategoryStatOut(
            category_id=row[0],
            category_name=row[1],
            play_count=row[2],
        )
        for row in result.all()
    ]
