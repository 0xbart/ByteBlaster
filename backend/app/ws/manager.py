from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket
from pydantic import BaseModel

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class WsClient:
    user_id: int
    username: str
    ip: str
    is_admin: bool = False
    is_superadmin: bool = False


class ConnectionManager:
    def __init__(self) -> None:
        # WebSocket → identity. A single user may have multiple sockets (tabs);
        # presence dedupes on user_id when building the public list.
        self._clients: dict[WebSocket, WsClient] = {}
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, client: WsClient) -> None:
        await ws.accept()
        async with self._lock:
            self._clients[ws] = client
        await self.broadcast_presence()

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.pop(ws, None)
        await self.broadcast_presence()

    def online_users(self) -> list[WsClient]:
        # Dedupe by user_id; ordering by username makes the UI list stable.
        seen: dict[int, WsClient] = {}
        for c in self._clients.values():
            seen.setdefault(c.user_id, c)
        return sorted(seen.values(), key=lambda c: c.username.lower())

    async def broadcast(self, event: BaseModel | dict[str, Any]) -> None:
        payload = event.model_dump(mode="json") if isinstance(event, BaseModel) else event
        async with self._lock:
            targets = list(self._clients.keys())
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception as exc:  # noqa: BLE001
                log.debug("Dropping dead WS connection: %s", exc)
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.pop(ws, None)

    async def broadcast_presence(self) -> None:
        # Local import to avoid a circular dep with schemas.
        from ..schemas import PresenceUser, WsPresenceEvent

        users = [
            PresenceUser(
                id=c.user_id,
                username=c.username,
                ip=c.ip,
                is_admin=c.is_admin,
                is_superadmin=c.is_superadmin,
            )
            for c in self.online_users()
        ]
        await self.broadcast(WsPresenceEvent(users=users))


manager = ConnectionManager()
