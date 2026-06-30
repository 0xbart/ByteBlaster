from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from .config import get_settings
from .routers import categories, editor, explore, global_mute, me, plays, sounds, stats, tags, users
from .services import ban as ban_service
from .ws import router as ws_router


def _operation_id(route: APIRoute) -> str:
    # Produces clean SDK function names like "getMe" instead of FastAPI's default.
    return route.name


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Re-arm auto-unban tasks for bans that outlived a backend restart.
    await ban_service.reschedule_all()
    yield


settings = get_settings()

app = FastAPI(
    title="ByteBlaster API",
    version="0.1.0",
    generate_unique_id_function=_operation_id,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me.router, prefix="/api")
app.include_router(sounds.router, prefix="/api")
app.include_router(plays.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(explore.router, prefix="/api")
app.include_router(global_mute.router, prefix="/api")
app.include_router(editor.router, prefix="/api")
app.include_router(ws_router.router)


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}
