from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "FrameVault"
APP_VERSION = "1.1.0"
ROOT_DIR = Path(__file__).resolve().parents[3]
STORAGE_DIR = ROOT_DIR / "storage"
MAX_UPLOAD_BYTES = int(os.getenv("FRAMEVAULT_MAX_UPLOAD_BYTES", 25 * 1024 * 1024))
MAX_VIDEO_UPLOAD_BYTES = int(
    os.getenv("FRAMEVAULT_MAX_VIDEO_UPLOAD_BYTES", 2 * 1024 * 1024 * 1024)
)
FFMPEG_PATH = os.getenv("FRAMEVAULT_FFMPEG_PATH", "ffmpeg")
FFPROBE_PATH = os.getenv("FRAMEVAULT_FFPROBE_PATH", "ffprobe")

DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
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
