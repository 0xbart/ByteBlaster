from __future__ import annotations

import ipaddress
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


async def require_admin(
    user: Annotated[User, Depends(require_user)],
) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only.")
    return user


CurrentUser = Annotated[User, Depends(require_user)]
AdminUser = Annotated[User, Depends(require_admin)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
