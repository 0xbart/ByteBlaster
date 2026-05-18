from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..deps import AdminUser, CurrentUser, DbSession
from ..models import Tag, sound_tags
from ..schemas import TagOut, WsTagRemovedEvent, WsTagRenamedEvent
from ..ws.manager import manager


class TagPatchIn(BaseModel):
    name: str = Field(min_length=1, max_length=32, pattern=r"^[a-z0-9_\- ]+$")

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagOut])
async def list_tags(_: CurrentUser, session: DbSession) -> list[TagOut]:
    # LEFT JOIN sound_tags so orphan tags (count=0) still appear.
    stmt = (
        select(Tag, func.count(sound_tags.c.sound_id).label("sound_count"))
        .outerjoin(sound_tags, sound_tags.c.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(Tag.name.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        TagOut(id=t.id, name=t.name, created_at=t.created_at, sound_count=cnt)
        for (t, cnt) in rows
    ]


@router.patch("/{tag_id}", response_model=TagOut)
async def rename_tag(
    tag_id: int,
    body: TagPatchIn,
    _: AdminUser,
    session: DbSession,
) -> TagOut:
    tag = await session.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    new_name = body.name.strip().lower()
    if new_name == tag.name:
        count_stmt = select(func.count(sound_tags.c.sound_id)).where(sound_tags.c.tag_id == tag.id)
        cnt = (await session.execute(count_stmt)).scalar_one()
        return TagOut(id=tag.id, name=tag.name, created_at=tag.created_at, sound_count=cnt)
    old_name = tag.name
    tag.name = new_name
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag '{new_name}' already exists.",
        ) from None
    await session.refresh(tag)
    count_stmt = select(func.count(sound_tags.c.sound_id)).where(sound_tags.c.tag_id == tag.id)
    cnt = (await session.execute(count_stmt)).scalar_one()
    await manager.broadcast(WsTagRenamedEvent(id=tag.id, old_name=old_name, new_name=tag.name))
    return TagOut(id=tag.id, name=tag.name, created_at=tag.created_at, sound_count=cnt)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int, _: AdminUser, session: DbSession) -> None:
    tag = await session.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    name = tag.name
    await session.delete(tag)
    await session.commit()
    # Inform other clients so they can strip the tag chip from cached sounds
    # without a full /sounds refetch.
    await manager.broadcast(WsTagRemovedEvent(name=name))
