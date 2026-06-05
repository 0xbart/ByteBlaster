from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings, get_settings
from ..db import get_session
from ..deps import client_ip
from ..models import User
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
        ),
    )
    # Send the current global-mute snapshot so a freshly opened tab
    # learns about an active mute without waiting for the next toggle.
    from ..services import global_mute as _gm
    from ..schemas import WsGlobalMuteEvent
    _state = _gm.state()
    try:
        await websocket.send_json(
            WsGlobalMuteEvent(active=_state.active, by=_state.by, at=_state.at).model_dump(mode="json")
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
            if isinstance(msg, dict) and msg.get("type") == "volume":
                try:
                    value = int(msg.get("value", 100))
                except (TypeError, ValueError):
                    continue
                await manager.set_volume(user.id, value)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
        await manager.forget_user_volume_if_offline(user.id)
