from __future__ import annotations

from fastapi import APIRouter

from ..deps import CurrentUser, MutemasterUser
from ..schemas import GlobalMuteSetIn, GlobalMuteState, WsGlobalMuteEvent
from ..services import global_mute
from ..ws.manager import manager

router = APIRouter(tags=["global-mute"])


@router.get("/global-mute", response_model=GlobalMuteState)
async def get_global_mute(_: CurrentUser) -> GlobalMuteState:
    return global_mute.state()


@router.post("/global-mute", response_model=GlobalMuteState)
async def set_global_mute(
    body: GlobalMuteSetIn,
    user: MutemasterUser,
) -> GlobalMuteState:
    new = await global_mute.set_state(body.active, user.username, body.duration_minutes)
    await manager.broadcast(
        WsGlobalMuteEvent(active=new.active, by=new.by, at=new.at, expires_at=new.expires_at)
    )
    return new
