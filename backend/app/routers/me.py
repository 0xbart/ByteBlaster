from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError

from ..deps import CurrentUser, DbSession, OptionalUser, SettingsDep, client_ip
from ..models import Category, Play, Sound, User, sound_favorites
from ..schemas import ClaimIn, MeOut, MeStatsOut, SoundStatOut, UserOut

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeOut)
async def get_me(
    request: Request,
    user: OptionalUser,
    settings: SettingsDep,
) -> MeOut:
    ip = client_ip(request, settings)
    return MeOut(
        user=UserOut.model_validate(user) if user else None,
        needs_claim=user is None,
        ip=ip,
    )


@router.get("/me/stats", response_model=MeStatsOut)
async def get_my_stats(user: CurrentUser, session: DbSession) -> MeStatsOut:
    now = datetime.now(tz=UTC)

    async def _plays_since(since: datetime | None) -> int:
        stmt = select(func.count(Play.id)).where(Play.played_by_user_id == user.id)
        if since is not None:
            stmt = stmt.where(Play.played_at >= since)
        return (await session.execute(stmt)).scalar_one()

    total_plays = await _plays_since(None)
    plays_day = await _plays_since(now - timedelta(days=1))
    plays_week = await _plays_since(now - timedelta(days=7))
    plays_month = await _plays_since(now - timedelta(days=30))

    favorites_count = (
        await session.execute(
            select(func.count())
            .select_from(sound_favorites)
            .where(sound_favorites.c.user_id == user.id)
        )
    ).scalar_one()

    sounds_uploaded = (
        await session.execute(
            select(func.count(Sound.id)).where(Sound.uploaded_by_user_id == user.id)
        )
    ).scalar_one()

    top_stmt = (
        select(
            Sound.id,
            Sound.display_name,
            Category.name,
            func.count(Play.id).label("play_count"),
        )
        .select_from(Sound)
        .join(Play, Play.sound_id == Sound.id)
        .outerjoin(Category, Category.id == Sound.category_id)
        .where(Play.played_by_user_id == user.id)
        .group_by(Sound.id, Category.name)
        .order_by(desc("play_count"), Sound.display_name)
        .limit(10)
    )
    top_rows = (await session.execute(top_stmt)).all()

    return MeStatsOut(
        total_plays=total_plays,
        plays_day=plays_day,
        plays_week=plays_week,
        plays_month=plays_month,
        favorites_count=favorites_count,
        sounds_uploaded=sounds_uploaded,
        member_since=user.created_at,
        top_sounds=[
            SoundStatOut(
                sound_id=row[0],
                display_name=row[1],
                category_name=row[2],
                play_count=row[3],
            )
            for row in top_rows
        ],
    )


@router.post("/me/claim", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def claim_username(
    body: ClaimIn,
    request: Request,
    user: OptionalUser,
    session: DbSession,
    settings: SettingsDep,
) -> User:
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This IP already has a claimed username.",
        )

    ip = client_ip(request, settings)
    if not ip:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No client IP.")

    existing = await session.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken."
        )

    # First user ever → superadmin. Race-safe enough because the unique-IP
    # constraint guarantees at most one concurrent winner.
    user_count = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    is_first = user_count == 0

    new_user = User(
        username=body.username,
        ip=ip,
        is_admin=is_first,
        is_superadmin=is_first,
    )
    session.add(new_user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or IP already claimed (race).",
        ) from None
    await session.refresh(new_user)
    return new_user
