from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import Settings, get_settings
from ..deps import ActiveUser, CurrentUser, MutemasterUser
from ..schemas import GlobalMuteSetIn, GlobalMuteState, WsGlobalMuteEvent, WsStopAllEvent
from ..services import global_mute, ratelimit
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


@router.post("/stop-all", status_code=204)
async def stop_all(
    user: ActiveUser,
    settings: Settings = Depends(get_settings),
) -> None:
    window = settings.rate_limit_stopall_window_seconds
    retry_in = ratelimit.check(
        "stopall", user.id, settings.rate_limit_stopall, window, exempt=user.is_superadmin
    )
    if retry_in is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit: max {settings.rate_limit_stopall} stop-all per {window}s. Try again in {retry_in}s.",
            headers={"Retry-After": str(retry_in)},
        )
    await manager.broadcast(WsStopAllEvent(by=user.username))
