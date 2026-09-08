from __future__ import annotations

import os


APP_NAME = "FrameVault"
APP_VERSION = "1.1.0"

DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def get_allowed_origins() -> list[str]:
    """
    Return the frontend origins allowed to call the API.

    FRAMEVAULT_ALLOWED_ORIGINS can contain a comma-separated list so
    development and deployment environments do not require code changes.
    """
    configured_origins = os.getenv("FRAMEVAULT_ALLOWED_ORIGINS")

    if not configured_origins:
        return list(DEFAULT_ALLOWED_ORIGINS)

    return [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ]