from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import MAX_UPLOAD_BYTES
from app.db import database
from app.ingestion.base import FrameCandidate


ROOT_DIR = Path(__file__).resolve().parents[3]
STORAGE_DIR = ROOT_DIR / "storage" / "uploads" / "images"
LOCAL_FILM_URL = "framevault://local-images"
ALLOWED_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}


class InvalidImageUpload(ValueError):
    pass


def _relative_path(path: Path) -> str:
    return str(path.relative_to(ROOT_DIR)).replace("\\", "/")


def ingest_uploaded_image(upload: UploadFile) -> dict:
    original_name = Path(upload.filename or "upload").name
    temporary_dir = STORAGE_DIR / ".tmp"
    temporary_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = temporary_dir / f"{id(upload)}.upload"
    digest = hashlib.sha256()
    size = 0

    try:
        with temporary_path.open("wb") as target:
            while chunk := upload.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise InvalidImageUpload(
                        f"Image exceeds the {MAX_UPLOAD_BYTES}-byte upload limit."
                    )
                digest.update(chunk)
                target.write(chunk)

        if size == 0:
            raise InvalidImageUpload("Uploaded image is empty.")

        try:
            with Image.open(temporary_path) as image:
                image.verify()
            with Image.open(temporary_path) as image:
                image_format = image.format
                width, height = image.size
        except (UnidentifiedImageError, OSError) as exc:
            raise InvalidImageUpload("Upload is not a valid supported image.") from exc

        if image_format not in ALLOWED_FORMATS:
            raise InvalidImageUpload("Only JPEG, PNG, and WebP images are supported.")

        mime_type, extension = ALLOWED_FORMATS[image_format]
        checksum = digest.hexdigest()
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        managed_path = STORAGE_DIR / f"{checksum}{extension}"
        if managed_path.exists():
            temporary_path.unlink()
        else:
            temporary_path.replace(managed_path)

        asset = database.upsert_media_asset(
            {
                "media_type": "image",
                "original_name": original_name,
                "mime_type": mime_type,
                "file_size": size,
                "checksum": checksum,
                "managed_path": _relative_path(managed_path),
                "source_type": "upload",
            }
        )
        film = database.upsert_film("Local Uploads", LOCAL_FILM_URL, None)
        frame = database.replace_film_frames(
            film["id"],
            [
                FrameCandidate(
                    source_type="upload",
                    source_identifier=checksum,
                    source_url=_relative_path(managed_path),
                    width=width,
                    height=height,
                    alt_text=original_name,
                    content_hash=checksum,
                    media_asset_id=asset["id"],
                ).to_record()
            ],
        )
        created_frame = next(item for item in frame if item["media_asset_id"] == asset["id"])
        return {"asset": asset, "frame": created_frame}
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
