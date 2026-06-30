from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..deps import AdminUser, DbSession
from ..models import User
from ..schemas import UserBanIn, UserOut, UserPatchIn, WsBannedEvent
from ..ws.manager import manager

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(_: AdminUser, session: DbSession) -> list[User]:
    result = await session.execute(select(User).order_by(User.id.asc()))
    return list(result.scalars().all())


@router.patch("/{user_id}", response_model=UserOut)
async def patch_user(
    user_id: int, body: UserPatchIn, caller: AdminUser, session: DbSession
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The superadmin cannot be modified.",
        )
    changes = body.model_dump(exclude_unset=True)
    if "is_mutemaster" in changes and not caller.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the superadmin can grant the mutemaster role.",
        )
    if "is_admin" in changes and changes["is_admin"] is not None:
        user.is_admin = bool(changes["is_admin"])
    if "is_mutemaster" in changes and changes["is_mutemaster"] is not None:
        user.is_mutemaster = bool(changes["is_mutemaster"])
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/{user_id}/ban", response_model=UserOut)
async def ban_user(
    user_id: int, body: UserBanIn, caller: AdminUser, session: DbSession
) -> User:
    if not caller.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the superadmin can ban users.",
        )
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The superadmin cannot be banned.",
        )
    if body.active:
        user.is_banned = True
        user.ban_expires_at = (
            datetime.now(tz=UTC) + timedelta(minutes=body.duration_minutes)
            if body.duration_minutes is not None
            else None
        )
    else:
        user.is_banned = False
        user.ban_expires_at = None
    await session.commit()
    await session.refresh(user)
    await manager.broadcast(
        WsBannedEvent(
            user_id=user.id,
            username=user.username,
            active=user.is_banned,
            expires_at=user.ban_expires_at,
            duration_minutes=body.duration_minutes if user.is_banned else None,
            by=caller.username,
        )
    )
    # Update Live users presence so the ban state shows there immediately.
    await manager.set_banned(user.id, user.is_banned)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, _: AdminUser, session: DbSession) -> None:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The superadmin cannot be deleted.",
        )
    await session.delete(user)
    await session.commit()
