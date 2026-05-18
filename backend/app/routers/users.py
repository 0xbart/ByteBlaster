from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..deps import AdminUser, DbSession
from ..models import User
from ..schemas import UserOut, UserPatchIn

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(_: AdminUser, session: DbSession) -> list[User]:
    result = await session.execute(select(User).order_by(User.id.asc()))
    return list(result.scalars().all())


@router.patch("/{user_id}", response_model=UserOut)
async def patch_user(
    user_id: int, body: UserPatchIn, _: AdminUser, session: DbSession
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The superadmin cannot be modified.",
        )
    user.is_admin = body.is_admin
    await session.commit()
    await session.refresh(user)
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
