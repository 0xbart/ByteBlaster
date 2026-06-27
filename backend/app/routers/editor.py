from __future__ import annotations

import re
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from pathlib import Path

from ..deps import ActiveUser, DbSession, SettingsDep
from ..models import Category, Sound
from ..schemas import EditorTrimIn, SoundOut, WsSoundAddedEvent
from ..services import editor as editor_service
from ..services.storage import resolve_local_path, resolve_path
from ..services.tags import get_or_create_tags
from ..ws.manager import manager

router = APIRouter(prefix="/editor", tags=["editor"])

# YouTube previews are served from an internal relative URL the editor can
# forward as `source_url`; resolve those to the on-disk file directly instead
# of HTTP-fetching ourselves (avoids loopback + http-only `_validate_url`).
_YT_PREVIEW_RE = re.compile(
    r"^/api/explore/youtube/preview/([A-Za-z0-9_\-]{8,40}\.mp3)$"
)
_YT_PREVIEW_SUBDIR = "_yt_previews"

# Local-library files are served same-origin; resolve to disk directly (same
# rationale as YouTube previews — avoids loopback + http-only _validate_url).
_LOCAL_FILE_RE = re.compile(r"^/api/explore/local/file\?rel=(.+)$")


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


def _to_out(sound: Sound) -> SoundOut:
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
        is_favorite=False,
        duration_ms=sound.duration_ms,
    )


@router.post("/trim", response_model=SoundOut)
async def trim_audio(
    body: EditorTrimIn,
    user: ActiveUser,
    session: DbSession,
    settings: SettingsDep,
) -> SoundOut:
    if (body.sound_id is None) == (body.source_url is None):
        raise HTTPException(
            status_code=422,
            detail="Provide exactly one of `sound_id` or `source_url`.",
        )

    if body.category_id is not None:
        if (await session.get(Category, body.category_id)) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown category_id {body.category_id}.",
            )

    tag_objs = await get_or_create_tags(session, body.tags)

    source: Path | str
    if body.sound_id is not None:
        src_sound = await session.get(Sound, body.sound_id)
        if src_sound is None:
            raise HTTPException(status_code=404, detail="Source sound not found.")
        source = resolve_path(src_sound.file_path, settings)
    else:
        assert body.source_url is not None
        preview_match = _YT_PREVIEW_RE.match(body.source_url)
        local_match = _LOCAL_FILE_RE.match(body.source_url)
        if preview_match is not None:
            preview = settings.storage_dir / _YT_PREVIEW_SUBDIR / preview_match.group(1)
            if not preview.is_file():
                raise HTTPException(
                    status_code=404,
                    detail="YouTube preview expired; re-fetch it first.",
                )
            source = preview
        elif local_match is not None:
            source = resolve_local_path(unquote(local_match.group(1)), settings)
        else:
            source = body.source_url

    stored = await editor_service.trim_to_storage(
        source, body.start_s, body.end_s, settings
    )

    sound = Sound(
        display_name=body.display_name.strip(),
        original_filename=None,
        file_path=str(stored.path),
        mime_type=stored.mime,
        size_bytes=stored.size,
        uploaded_by_user_id=user.id,
        category_id=body.category_id,
        duration_ms=stored.duration_ms,
    )
    sound.tags = tag_objs
    session.add(sound)
    await session.commit()
    full = await _load_full(session, sound.id)
    assert full is not None

    out = _to_out(full)
    await manager.broadcast(WsSoundAddedEvent(sound=out, by=user.username))
    return out
