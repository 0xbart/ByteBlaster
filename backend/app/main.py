from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from .config import get_settings
from .routers import categories, explore, me, plays, sounds, stats, tags, users
from .ws import router as ws_router


def _operation_id(route: APIRoute) -> str:
    # Produces clean SDK function names like "getMe" instead of FastAPI's default.
    return route.name


settings = get_settings()

app = FastAPI(
    title="ByteBlaster API",
    version="0.1.0",
    generate_unique_id_function=_operation_id,
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
app.include_router(ws_router.router)


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}
