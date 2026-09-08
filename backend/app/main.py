from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import films, frames, health, ingestion
from app.core.config import (
    APP_NAME,
    APP_VERSION,
    get_allowed_origins,
)
from app.db import database


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
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

    return app


app = create_app()


@app.on_event("startup")
def startup() -> None:
    database.init_db()