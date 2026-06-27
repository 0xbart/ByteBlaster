"""Shared in-memory sliding-window rate limiter.

Keyed by (bucket, user_id) so several endpoints (play, stop-all, vote) can each
keep an independent window. Single-process only — fine for office-scale, like
``votes`` and ``global_mute``.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

# (bucket, user_id) -> deque of recent hit timestamps (monotonic seconds).
_recent: dict[tuple[str, int], deque[float]] = defaultdict(deque)


def check(
    bucket: str,
    user_id: int,
    limit: int,
    window: float,
    *,
    exempt: bool = False,
) -> int | None:
    """Register a hit and enforce the window.

    Returns ``None`` when allowed (and records the hit), or the number of
    seconds to wait (``retry_in``) when the limit is exceeded. ``limit <= 0``
    disables the check; ``exempt`` callers (e.g. superadmin) are never limited.
    """
    if exempt or limit <= 0:
        return None
    now = time.monotonic()
    cutoff = now - window
    hits = _recent[(bucket, user_id)]
    while hits and hits[0] < cutoff:
        hits.popleft()
    if len(hits) >= limit:
        return max(0, int(window - (now - hits[0]) + 1))
    hits.append(now)
    return None
