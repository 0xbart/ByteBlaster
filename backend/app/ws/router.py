from __future__ import annotations

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
    try:
        while True:
            # We don't expect client messages, but keep the loop alive so disconnect is detected.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
