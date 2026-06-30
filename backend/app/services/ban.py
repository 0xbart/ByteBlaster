"""Auto-expiry for timed bans.

A timed ban is stored in the DB (``User.is_banned`` / ``User.ban_expires_at``).
``deps.py`` clears an elapsed ban lazily on the user's next request, but that
path is silent: no broadcast, no presence update, no activity entry. This
service schedules a background task per timed ban that, on expiry, clears the
ban in a fresh session and broadcasts an ``active=false`` event (with no actor)
so every client updates its Live users list and activity feed.

Single-worker office deployment: tasks live in this process. ``reschedule_all``
re-arms them after a backend restart.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy import select

from ..db import SessionLocal
from ..models import User

_tasks: dict[int, asyncio.Task] = {}


def cancel(user_id: int) -> None:
    """Cancel a pending auto-unban (e.g. on manual unban or re-ban)."""
    task = _tasks.pop(user_id, None)
    if task is not None and not task.done():
        task.cancel()


def schedule(user_id: int, expires_at: datetime) -> None:
    """(Re)arm an auto-unban for ``user_id`` at ``expires_at``."""
    cancel(user_id)
    delay = (expires_at - datetime.now(tz=UTC)).total_seconds()
    _tasks[user_id] = asyncio.create_task(_auto_unban(user_id, max(0.0, delay)))


async def _auto_unban(user_id: int, delay_seconds: float) -> None:
    try:
        await asyncio.sleep(delay_seconds)
    except asyncio.CancelledError:
        return
    # Local imports avoid a circular dependency at module load.
    from ..schemas import WsBannedEvent
    from ..ws.manager import manager

    async with SessionLocal() as session:
        user = await session.get(User, user_id)
        if user is None or not user.is_banned:
            return
        # Guard against clock races / rescheduling: only lift if actually due.
        if user.ban_expires_at is not None and user.ban_expires_at > datetime.now(tz=UTC):
            schedule(user_id, user.ban_expires_at)
            return
        user.is_banned = False
        user.ban_expires_at = None
        await session.commit()
        username = user.username

    _tasks.pop(user_id, None)
    # by=None marks an automatic (timed) unban so the feed shows a generic notice.
    await manager.broadcast(
        WsBannedEvent(user_id=user_id, username=username, active=False, by=None)
    )
    await manager.set_banned(user_id, False)


async def reschedule_all() -> None:
    """Re-arm auto-unban tasks for all currently timed-banned users (startup)."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.is_banned.is_(True), User.ban_expires_at.is_not(None))
        )
        users = list(result.scalars().all())
    for user in users:
        if user.ban_expires_at is not None:
            schedule(user.id, user.ban_expires_at)
