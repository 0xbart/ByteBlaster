"""In-memory global-mute state (single-worker office deployment).

Backend restart resets the state to inactive. Auto-unmute is implemented
as a single cancelable asyncio task.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from ..schemas import GlobalMuteState

_lock = asyncio.Lock()
_state: dict[str, object] = {
    "active": False,
    "by": None,
    "at": None,
    "expires_at": None,
}
_expiry_task: asyncio.Task | None = None


def state() -> GlobalMuteState:
    return GlobalMuteState(
        active=bool(_state["active"]),
        by=_state["by"],  # type: ignore[arg-type]
        at=_state["at"],  # type: ignore[arg-type]
        expires_at=_state["expires_at"],  # type: ignore[arg-type]
    )


async def _broadcast_state() -> None:
    # Local import to avoid circular dependency.
    from ..ws.manager import manager
    from ..schemas import WsGlobalMuteEvent

    s = state()
    await manager.broadcast(
        WsGlobalMuteEvent(active=s.active, by=s.by, at=s.at, expires_at=s.expires_at)
    )


async def _auto_unmute(delay_seconds: float) -> None:
    try:
        await asyncio.sleep(delay_seconds)
    except asyncio.CancelledError:
        return
    async with _lock:
        if not _state["active"]:
            return
        _state["active"] = False
        _state["by"] = None
        _state["at"] = None
        _state["expires_at"] = None
    await _broadcast_state()


def _cancel_expiry() -> None:
    global _expiry_task
    if _expiry_task is not None and not _expiry_task.done():
        _expiry_task.cancel()
    _expiry_task = None


async def set_state(
    active: bool, by: str, duration_minutes: int | None = None
) -> GlobalMuteState:
    """Update mute state; returns the new snapshot.

    The caller is responsible for broadcasting the new state to clients.
    """
    global _expiry_task
    _cancel_expiry()
    now = datetime.now(tz=UTC)
    async with _lock:
        _state["active"] = bool(active)
        # Record who toggled it; on auto-expire the background task sets
        # `by` back to None so the frontend can distinguish manual vs auto.
        _state["by"] = by
        _state["at"] = now if active else None
        if active and duration_minutes and duration_minutes > 0:
            _state["expires_at"] = now + timedelta(minutes=int(duration_minutes))
        else:
            _state["expires_at"] = None
    if active and duration_minutes and duration_minutes > 0:
        _expiry_task = asyncio.create_task(_auto_unmute(duration_minutes * 60))
    return state()
