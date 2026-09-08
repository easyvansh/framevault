from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import films, frames, health, ingestion
from app.core.config import (
    APP_NAME,
    APP_VERSION,
    get_allowed_origins,
    STORAGE_DIR,
)
from app.db import database


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(films.router)
    app.include_router(frames.router)
    app.include_router(ingestion.router)
    app.mount(
        "/storage",
        StaticFiles(directory=str(STORAGE_DIR), check_dir=False),
        name="storage",
    )

    return app


app = create_app()
