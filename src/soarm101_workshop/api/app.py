from __future__ import annotations

import contextlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import processes, rigs
from .service import manager
from .settings import get_settings


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    killed = await manager.reconcile()
    if killed:
        print(f"Reaped {killed} orphaned process group(s) from a previous run.", flush=True)
    yield
    await manager.stop_all()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="SO-ARM101 Workshop API", version=rigs.VERSION, lifespan=lifespan)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(rigs.router)
    app.include_router(processes.router)
    static_dir = Path(__file__).parent.parent / "web" / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    return app


def run() -> None:
    import uvicorn

    s = get_settings()
    if not s.token and not s.allow_localhost_no_auth:
        print(
            "WARNING: no SOARM_API_TOKEN set and loopback bypass disabled — "
            "all /api calls will 401."
        )
    uvicorn.run(create_app(), host=s.host, port=s.port, workers=1)
