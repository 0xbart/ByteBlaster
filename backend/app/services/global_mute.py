"""In-memory global-mute state (single-worker office deployment).

Backend restart resets the state to inactive.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from ..schemas import GlobalMuteState

_lock = asyncio.Lock()
_state: dict[str, object] = {"active": False, "by": None, "at": None}


def state() -> GlobalMuteState:
    return GlobalMuteState(
        active=bool(_state["active"]),
        by=_state["by"],  # type: ignore[arg-type]
        at=_state["at"],  # type: ignore[arg-type]
    )


async def set_state(active: bool, by: str) -> GlobalMuteState:
    async with _lock:
        _state["active"] = bool(active)
        _state["by"] = by if active else None
        _state["at"] = datetime.now(tz=UTC) if active else None
    return state()
