"""Ephemeral, in-memory thumbs up/down voting on recent plays.

A play opens a short voting window; votes within it are tallied and broadcast
but never persisted. Backend restart drops all windows (by design). Single
worker only — fine for office-scale, like global_mute.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from ..schemas import VoteVoter, WsVoteEvent

# Window stays open a few seconds past the client's 20s countdown so a click
# fired just before the popup dismisses still lands.
WINDOW_SECONDS = 25.0

_lock = asyncio.Lock()
# play_id -> {user_id: VoteVoter}
_windows: dict[int, dict[int, VoteVoter]] = {}


def register_play(play_id: int) -> None:
    """Open a voting window for a freshly broadcast play."""
    _windows[play_id] = {}
    asyncio.create_task(_expire(play_id))


async def _expire(play_id: int) -> None:
    try:
        await asyncio.sleep(WINDOW_SECONDS)
    except asyncio.CancelledError:
        return
    async with _lock:
        _windows.pop(play_id, None)


async def record_vote(
    play_id: int, user_id: int, username: str, direction: str
) -> WsVoteEvent | None:
    """Upsert a user's vote; return the new tally event, or None if ignored.

    Re-clicking the same direction toggles the vote off. Votes for an unknown
    or expired play window are ignored (returns None).
    """
    async with _lock:
        window = _windows.get(play_id)
        if window is None:
            return None
        existing = window.get(user_id)
        if existing is not None and existing.direction == direction:
            del window[user_id]  # toggle off
        else:
            window[user_id] = VoteVoter(username=username, direction=direction)
        voters = list(window.values())

    up = sum(1 for v in voters if v.direction == "up")
    down = sum(1 for v in voters if v.direction == "down")
    return WsVoteEvent(
        play_id=play_id,
        by=username,
        direction=direction,  # type: ignore[arg-type]
        up=up,
        down=down,
        voters=voters,
        at=datetime.now(tz=UTC),
    )
