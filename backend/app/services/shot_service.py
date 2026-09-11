from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from app.core.config import FFMPEG_PATH, SHOT_DETECTION_THRESHOLD
from app.db import database
from app.ingestion.base import FrameCandidate


ROOT_DIR = Path(__file__).resolve().parents[3]
KEYFRAME_DIR = ROOT_DIR / "storage" / "keyframes"
LOCAL_VIDEO_FILM_URL = "framevault://video-keyframes"
PTS_PATTERN = re.compile(r"pts_time:([0-9]+(?:\.[0-9]+)?)")


class ShotExtractionUnavailable(RuntimeError):
    pass


class ShotExtractionFailed(RuntimeError):
    pass


def _video_path(asset: dict) -> Path:
    path = ROOT_DIR / asset["managed_path"]
    if not path.is_file():
        raise ShotExtractionFailed("The managed video file is missing.")
    return path


def _detect_boundaries(path: Path, duration_ms: int, threshold: float) -> list[int]:
    expression = f"select=gt(scene\\,{threshold}),showinfo"
    completed = subprocess.run(
        [FFMPEG_PATH, "-hide_banner", "-i", str(path), "-vf", expression, "-an", "-f", "null", "-"],
        capture_output=True,
        text=True,
        timeout=3600,
        check=False,
    )
    if completed.returncode != 0:
        raise ShotExtractionFailed(f"Shot detection failed: {completed.stderr.strip()}")
    detected = [round(float(value) * 1000) for value in PTS_PATTERN.findall(completed.stderr)]
    return sorted({0, duration_ms, *(value for value in detected if 0 < value < duration_ms)})


def _extract_keyframe(path: Path, target: Path, timestamp_ms: int) -> None:
    completed = subprocess.run(
        [
            FFMPEG_PATH, "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{timestamp_ms / 1000:.3f}", "-i", str(path),
            "-frames:v", "1", "-q:v", "2", str(target),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0 or not target.is_file():
        raise ShotExtractionFailed(f"Keyframe extraction failed: {completed.stderr.strip()}")


def extract_video_shots(media_asset_id: int, threshold: float = SHOT_DETECTION_THRESHOLD) -> list[dict]:
    if not 0 < threshold < 1:
        raise ValueError("Shot threshold must be between 0 and 1.")
    asset = database.get_media_asset(media_asset_id)
    if not asset or asset["media_type"] != "video":
        raise LookupError("Video media asset not found.")
    if not shutil.which(FFMPEG_PATH):
        raise ShotExtractionUnavailable("FFmpeg is required for shot detection and keyframe extraction.")
    duration_ms = asset.get("duration_ms")
    if not duration_ms or duration_ms <= 0:
        raise ShotExtractionFailed("The video has no usable duration metadata.")

    path = _video_path(asset)
    boundaries = _detect_boundaries(path, duration_ms, threshold)
    KEYFRAME_DIR.mkdir(parents=True, exist_ok=True)
    film = database.upsert_film("Video Keyframes", LOCAL_VIDEO_FILM_URL, None)
    records = []
    for index, (start_ms, end_ms) in enumerate(zip(boundaries, boundaries[1:])):
        timestamp_ms = start_ms + (end_ms - start_ms) // 2
        keyframe_path = KEYFRAME_DIR / f"{asset['checksum']}-shot-{index:04d}.jpg"
        _extract_keyframe(path, keyframe_path, timestamp_ms)
        content = keyframe_path.read_bytes()
        checksum = hashlib.sha256(content).hexdigest()
        with Image.open(keyframe_path) as image:
            width, height = image.size
        relative_path = str(keyframe_path.relative_to(ROOT_DIR)).replace("\\", "/")
        keyframe_asset = database.upsert_media_asset({
            "media_type": "image", "original_name": keyframe_path.name,
            "mime_type": "image/jpeg", "file_size": len(content), "checksum": checksum,
            "managed_path": relative_path, "source_type": "video_keyframe",
            "width": width, "height": height,
            "metadata": {"video_asset_id": media_asset_id, "timestamp_ms": timestamp_ms},
        })
        frames = database.replace_film_frames(film["id"], [FrameCandidate(
            source_type="video_keyframe",
            source_identifier=f"{asset['checksum']}:{index}",
            source_url=relative_path,
            width=width,
            height=height,
            alt_text=f"{asset['original_name']} shot {index + 1}",
            content_hash=checksum,
            media_asset_id=keyframe_asset["id"],
        ).to_record()])
        frame = next(item for item in frames if item["source_identifier"] == f"{asset['checksum']}:{index}")
        records.append({
            "shot_index": index, "start_ms": start_ms, "end_ms": end_ms,
            "keyframe_frame_id": frame["id"], "threshold": threshold,
        })
    return database.replace_shots(media_asset_id, records)
