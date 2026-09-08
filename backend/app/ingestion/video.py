from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from fastapi import UploadFile

from app.core.config import FFPROBE_PATH, MAX_VIDEO_UPLOAD_BYTES
from app.db import database


ROOT_DIR = Path(__file__).resolve().parents[3]
STORAGE_DIR = ROOT_DIR / "storage" / "uploads" / "videos"
ALLOWED_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm"}


class InvalidVideoUpload(ValueError):
    pass


class VideoToolUnavailable(RuntimeError):
    pass


def _relative_path(path: Path) -> str:
    return str(path.relative_to(ROOT_DIR)).replace("\\", "/")


def _parse_rate(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    numerator, _, denominator = value.partition("/")
    try:
        return float(numerator) / float(denominator or 1)
    except (ValueError, ZeroDivisionError):
        return None


def probe_video(path: Path) -> dict:
    if not shutil.which(FFPROBE_PATH):
        raise VideoToolUnavailable(
            "FFprobe is required for video ingestion. Install FFmpeg or set "
            "FRAMEVAULT_FFPROBE_PATH."
        )
    completed = subprocess.run(
        [FFPROBE_PATH, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise InvalidVideoUpload(
            f"Video metadata could not be read: {completed.stderr.strip()}"
        )
    try:
        payload = json.loads(completed.stdout)
        stream = next(
            item for item in payload.get("streams", []) if item.get("codec_type") == "video"
        )
        duration = stream.get("duration") or payload.get("format", {}).get("duration")
        return {
            "width": int(stream["width"]),
            "height": int(stream["height"]),
            "duration_ms": round(float(duration) * 1000),
            "frame_rate": _parse_rate(stream.get("avg_frame_rate")),
            "probe": payload,
        }
    except (KeyError, StopIteration, TypeError, ValueError) as exc:
        raise InvalidVideoUpload("Upload does not contain a readable video stream.") from exc


def ingest_uploaded_video(upload: UploadFile) -> dict:
    if not shutil.which(FFPROBE_PATH):
        raise VideoToolUnavailable(
            "FFprobe is required for video ingestion. Install FFmpeg or set "
            "FRAMEVAULT_FFPROBE_PATH."
        )
    original_name = Path(upload.filename or "video").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise InvalidVideoUpload("Only MP4, MOV, MKV, and WebM videos are supported.")

    temporary_dir = STORAGE_DIR / ".tmp"
    temporary_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = temporary_dir / f"{id(upload)}{suffix}"
    digest = hashlib.sha256()
    size = 0
    try:
        with temporary_path.open("wb") as target:
            while chunk := upload.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_VIDEO_UPLOAD_BYTES:
                    raise InvalidVideoUpload("Video exceeds the configured upload limit.")
                digest.update(chunk)
                target.write(chunk)
        if size == 0:
            raise InvalidVideoUpload("Uploaded video is empty.")

        metadata = probe_video(temporary_path)
        checksum = digest.hexdigest()
        managed_path = STORAGE_DIR / f"{checksum}{suffix}"
        if managed_path.exists():
            temporary_path.unlink()
        else:
            temporary_path.replace(managed_path)

        return database.upsert_media_asset(
            {
                "media_type": "video",
                "original_name": original_name,
                "mime_type": upload.content_type or "application/octet-stream",
                "file_size": size,
                "checksum": checksum,
                "managed_path": _relative_path(managed_path),
                "source_type": "upload",
                "width": metadata["width"],
                "height": metadata["height"],
                "duration_ms": metadata["duration_ms"],
                "frame_rate": metadata["frame_rate"],
                "metadata": metadata["probe"],
            }
        )
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
