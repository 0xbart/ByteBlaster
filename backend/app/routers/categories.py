from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..deps import AdminUser, CurrentUser, DbSession
from ..models import Category, Sound
from ..schemas import CategoryIn, CategoryOut, WsCategoryRenamedEvent
from ..ws.manager import manager

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(_: CurrentUser, session: DbSession) -> list[CategoryOut]:
    # LEFT JOIN sounds so empty categories still appear with count 0.
    stmt = (
        select(Category, func.count(Sound.id).label("sound_count"))
        .outerjoin(Sound, Sound.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.name.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        CategoryOut(id=c.id, name=c.name, created_at=c.created_at, sound_count=cnt)
        for (c, cnt) in rows
    ]


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryIn, _: AdminUser, session: DbSession
) -> CategoryOut:
    name = body.name.strip()
    cat = Category(name=name)
    session.add(cat)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{name}' already exists.",
        ) from None
    await session.refresh(cat)
    return CategoryOut(id=cat.id, name=cat.name, created_at=cat.created_at, sound_count=0)


@router.patch("/{category_id}", response_model=CategoryOut)
async def rename_category(
    category_id: int,
    body: CategoryIn,
    _: AdminUser,
    session: DbSession,
) -> CategoryOut:
    cat = await session.get(Category, category_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    new_name = body.name.strip()
    if new_name == cat.name:
        # No-op rename — return current sound count.
        count_stmt = select(func.count(Sound.id)).where(Sound.category_id == cat.id)
        cnt = (await session.execute(count_stmt)).scalar_one()
        return CategoryOut(id=cat.id, name=cat.name, created_at=cat.created_at, sound_count=cnt)
    cat.name = new_name
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{new_name}' already exists.",
        ) from None
    await session.refresh(cat)
    count_stmt = select(func.count(Sound.id)).where(Sound.category_id == cat.id)
    cnt = (await session.execute(count_stmt)).scalar_one()
    await manager.broadcast(WsCategoryRenamedEvent(id=cat.id, new_name=cat.name))
    return CategoryOut(id=cat.id, name=cat.name, created_at=cat.created_at, sound_count=cnt)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int, _: AdminUser, session: DbSession
) -> None:
    cat = await session.get(Category, category_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await session.delete(cat)
    await session.commit()
