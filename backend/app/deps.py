from __future__ import annotations

import ipaddress
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated, Protocol, runtime_checkable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings, get_settings
from .db import get_session
from .models import User


@runtime_checkable
class _HasClient(Protocol):
    @property
    def client(self) -> object | None: ...
    @property
    def headers(self) -> object: ...


@lru_cache(maxsize=1)
def _trusted_networks(spec: tuple[str, ...]) -> tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]:
    networks = []
    for item in spec:
        try:
            networks.append(ipaddress.ip_network(item.strip(), strict=False))
        except ValueError:
            continue
    return tuple(networks)


def _is_trusted(peer: str, settings: Settings) -> bool:
    if not peer or not settings.trusted_proxies:
        return False
    try:
        ip = ipaddress.ip_address(peer)
    except ValueError:
        return False
    return any(ip in net for net in _trusted_networks(tuple(settings.trusted_proxies)))


def client_ip(conn: Request | _HasClient, settings: Settings) -> str:
    peer = getattr(getattr(conn, "client", None), "host", "") or ""
    if _is_trusted(peer, settings):
        forwarded = conn.headers.get("x-forwarded-for")  # type: ignore[union-attr]
        if forwarded:
            # Take the first (originating) entry; subsequent entries are this proxy chain.
            return forwarded.split(",")[0].strip()
    return peer


async def get_current_user_optional(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User | None:
    ip = client_ip(request, settings)
    if not ip:
        return None
    result = await session.execute(select(User).where(User.ip == ip))
    return result.scalar_one_or_none()


async def require_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "needs_claim", "message": "Unknown IP — claim a username first"},
        )
    return user


async def ban_is_active(user: User, session: AsyncSession) -> bool:
    """Return whether ``user`` is currently banned, lazily clearing an expired ban.

    A superadmin can never be banned. A ban with ``ban_expires_at`` in the past is
    cleared (and committed) so the user is unbanned from now on.
    """
    if user.is_superadmin or not user.is_banned:
        return False
    if user.ban_expires_at is not None and user.ban_expires_at <= datetime.now(tz=UTC):
        user.is_banned = False
        user.ban_expires_at = None
        await session.commit()
        return False
    return True


async def require_unbanned(
    user: Annotated[User, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if await ban_is_active(user, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "banned",
                "message": "You are banned.",
                "expires_at": user.ban_expires_at.isoformat() if user.ban_expires_at else None,
            },
        )
    return user


async def require_admin(
    user: Annotated[User, Depends(require_user)],
) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only.")
    return user


async def require_mutemaster(
    user: Annotated[User, Depends(require_user)],
) -> User:
    if not (user.is_mutemaster or user.is_superadmin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mutemaster only.")
    return user


CurrentUser = Annotated[User, Depends(require_user)]
ActiveUser = Annotated[User, Depends(require_unbanned)]
AdminUser = Annotated[User, Depends(require_admin)]
MutemasterUser = Annotated[User, Depends(require_mutemaster)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
