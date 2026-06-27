from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings, get_settings
from ..db import get_session
from ..deps import ban_is_active, client_ip
from ..models import User
from ..schemas import WsRateLimitEvent, WsSetThemeIn, WsThemeSetEvent, WsVoteIn
from ..services import ratelimit, votes
from .manager import WsClient, manager

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(
    websocket: WebSocket,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    ip = client_ip(websocket, settings)  # type: ignore[arg-type]
    if not ip:
        await websocket.close(code=4401)
        return
    user = (await session.execute(select(User).where(User.ip == ip))).scalar_one_or_none()
    if user is None:
        await websocket.close(code=4401)
        return

    await manager.connect(
        websocket,
        WsClient(
            user_id=user.id,
            username=user.username,
            ip=str(user.ip),
            is_admin=user.is_admin,
            is_superadmin=user.is_superadmin,
            is_banned=user.is_banned,
        ),
    )
    # Send the current global-mute snapshot so a freshly opened tab
    # learns about an active mute without waiting for the next toggle.
    from ..services import global_mute as _gm
    from ..schemas import WsGlobalMuteEvent
    _state = _gm.state()
    try:
        await websocket.send_json(
            WsGlobalMuteEvent(
                active=_state.active, by=_state.by, at=_state.at, expires_at=_state.expires_at
            ).model_dump(mode="json")
        )
    except Exception:  # noqa: BLE001
        pass
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except (ValueError, TypeError):
                continue
            if not isinstance(msg, dict):
                continue
            mtype = msg.get("type")
            if mtype == "volume":
                try:
                    value = int(msg.get("value", 100))
                except (TypeError, ValueError):
                    continue
                await manager.set_volume(user.id, value)
            elif mtype == "set_theme":
                # Superadmin-only; cannot target self.
                if not user.is_superadmin:
                    continue
                try:
                    req = WsSetThemeIn.model_validate(msg)
                except ValidationError:
                    continue
                if req.target_user_id == user.id:
                    continue
                await manager.send_to_user(
                    req.target_user_id,
                    WsThemeSetEvent(mode=req.mode, skin=req.skin, by=user.username),
                )
            elif mtype == "vote":
                try:
                    vote = WsVoteIn.model_validate(msg)
                except ValidationError:
                    continue
                # Banned users cannot vote (superadmin is never banned).
                if await ban_is_active(user, session):
                    continue
                retry_in = ratelimit.check(
                    "vote",
                    user.id,
                    settings.rate_limit_votes,
                    settings.rate_limit_votes_window_seconds,
                    exempt=user.is_superadmin,
                )
                if retry_in is not None:
                    await manager.send_to_user(
                        user.id, WsRateLimitEvent(scope="vote", retry_in=retry_in)
                    )
                    continue
                event = await votes.record_vote(
                    vote.play_id, user.id, user.username, vote.direction
                )
                if event is not None:
                    await manager.broadcast(event)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
        await manager.forget_user_volume_if_offline(user.id)
