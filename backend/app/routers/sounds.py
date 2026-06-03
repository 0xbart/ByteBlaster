from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from ..deps import AdminUser, CurrentUser, DbSession, SettingsDep
from ..models import Category, Sound, sound_favorites
from ..schemas import SoundOut, SoundPatchIn, WsSoundAddedEvent, WsSoundRemovedEvent, WsSoundUpdatedEvent
from ..services import storage
from ..services.download import derive_filename_from_url, download_url
from ..services.tags import get_or_create_tags
from ..ws.manager import manager

router = APIRouter(prefix="/sounds", tags=["sounds"])


def _to_out(sound: Sound, favorite_ids: set[int] | frozenset[int] = frozenset()) -> SoundOut:
    return SoundOut(
        id=sound.id,
        display_name=sound.display_name,
        mime_type=sound.mime_type,
        size_bytes=sound.size_bytes,
        uploaded_by_user_id=sound.uploaded_by_user_id,
        uploader_username=sound.uploader.username,
        category_id=sound.category_id,
        category_name=sound.category.name if sound.category else None,
        tags=sorted(t.name for t in sound.tags),
        created_at=sound.created_at,
        url=f"/api/sounds/{sound.id}/file",
        is_favorite=sound.id in favorite_ids,
    )


async def _is_fav(session, user_id: int, sound_id: int) -> bool:
    r = await session.execute(
        select(sound_favorites.c.sound_id)
        .where(
            sound_favorites.c.user_id == user_id,
            sound_favorites.c.sound_id == sound_id,
        )
        .limit(1)
    )
    return r.first() is not None


async def _load_full(session, sound_id: int) -> Sound | None:
    result = await session.execute(
        select(Sound)
        .options(
            selectinload(Sound.uploader),
            selectinload(Sound.category),
            selectinload(Sound.tags),
        )
        .where(Sound.id == sound_id)
    )
    return result.scalar_one_or_none()


@router.get("", response_model=list[SoundOut])
async def list_sounds(session: DbSession, user: CurrentUser) -> list[SoundOut]:
    result = await session.execute(
        select(Sound)
        .options(
            selectinload(Sound.uploader),
            selectinload(Sound.category),
            selectinload(Sound.tags),
        )
        .order_by(Sound.created_at.desc())
    )
    fav_rows = await session.execute(
        select(sound_favorites.c.sound_id).where(sound_favorites.c.user_id == user.id)
    )
    fav_ids = {row[0] for row in fav_rows.all()}
    return [_to_out(s, fav_ids) for s in result.scalars().all()]


@router.post("", response_model=SoundOut, status_code=status.HTTP_201_CREATED)
async def upload_sound(
    user: CurrentUser,
    session: DbSession,
    settings: SettingsDep,
    file: UploadFile | None = File(None),
    url: str | None = Form(None),
    display_name: str = Form(..., min_length=1, max_length=120),
    category_id: int | None = Form(None),
    tags: list[str] = Form([]),
) -> SoundOut:
    # Exactly one source must be provided.
    if (file is None) == (not url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide exactly one of `file` or `url`.",
        )

    if category_id is not None:
        if (await session.get(Category, category_id)) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown category_id {category_id}.",
            )

    # Validate + normalize tags before touching storage so a 422 doesn't leak a file.
    tag_objs = await get_or_create_tags(session, tags)

    if file is not None:
        stored = await storage.save_upload(file, settings)
        original_filename = file.filename
    else:
        assert url is not None
        stored = await download_url(url, settings)
        original_filename = derive_filename_from_url(url)

    sound = Sound(
        display_name=display_name.strip(),
        original_filename=original_filename,
        file_path=str(stored.path),
        mime_type=stored.mime,
        size_bytes=stored.size,
        uploaded_by_user_id=user.id,
        category_id=category_id,
    )
    sound.tags = tag_objs
    session.add(sound)
    await session.commit()
    full = await _load_full(session, sound.id)
    assert full is not None  # just inserted

    out = _to_out(full)
    await manager.broadcast(WsSoundAddedEvent(sound=out, by=user.username))
    return out


@router.patch("/{sound_id}", response_model=SoundOut)
async def patch_sound(
    sound_id: int,
    body: SoundPatchIn,
    user: AdminUser,
    session: DbSession,
) -> SoundOut:
    sound = await _load_full(session, sound_id)
    if sound is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    changes = body.model_dump(exclude_unset=True)
    if "display_name" in changes and changes["display_name"] is not None:
        sound.display_name = changes["display_name"].strip()
    if "category_id" in changes:
        new_cat = changes["category_id"]
        if new_cat is not None:
            if (await session.get(Category, new_cat)) is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown category_id {new_cat}.",
                )
        sound.category_id = new_cat
    if "tags" in changes and changes["tags"] is not None:
        sound.tags = await get_or_create_tags(session, changes["tags"])

    await session.commit()
    # expire_on_commit=False means attributes aren't auto-refreshed; explicitly
    # reload relationships so the broadcast reflects the new state.
    await session.refresh(sound, ["uploader", "category", "tags"])
    out = _to_out(sound)
    await manager.broadcast(WsSoundUpdatedEvent(sound=out, by=user.username))
    return out


@router.delete("/{sound_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sound(sound_id: int, user: CurrentUser, session: DbSession) -> None:
    sound = await session.get(Sound, sound_id)
    if sound is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if sound.uploaded_by_user_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the uploader or an admin can delete this sound.",
        )
    display_name = sound.display_name
    await session.delete(sound)
    await session.commit()
    await manager.broadcast(
        WsSoundRemovedEvent(
            sound_id=sound_id,
            display_name=display_name,
            by=user.username,
        )
    )


@router.post("/{sound_id}/favorite", response_model=SoundOut)
async def favorite_sound(
    sound_id: int, user: CurrentUser, session: DbSession
) -> SoundOut:
    sound = await _load_full(session, sound_id)
    if sound is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    stmt = (
        pg_insert(sound_favorites)
        .values(user_id=user.id, sound_id=sound_id)
        .on_conflict_do_nothing(index_elements=["user_id", "sound_id"])
    )
    await session.execute(stmt)
    await session.commit()
    return _to_out(sound, frozenset({sound_id}))


@router.delete("/{sound_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def unfavorite_sound(
    sound_id: int, user: CurrentUser, session: DbSession
) -> None:
    sound = await session.get(Sound, sound_id)
    if sound is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await session.execute(
        delete(sound_favorites).where(
            sound_favorites.c.user_id == user.id,
            sound_favorites.c.sound_id == sound_id,
        )
    )
    await session.commit()


@router.get("/{sound_id}/file")
async def get_sound_file(
    sound_id: int, _: CurrentUser, session: DbSession, settings: SettingsDep
) -> FileResponse:
    sound = await session.get(Sound, sound_id)
    if sound is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    path = storage.resolve_path(sound.file_path, settings)
    return FileResponse(path, media_type=sound.mime_type, filename=sound.original_filename or path.name)
