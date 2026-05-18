from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..deps import DbSession, OptionalUser, SettingsDep, client_ip
from ..models import User
from ..schemas import ClaimIn, MeOut, UserOut

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
