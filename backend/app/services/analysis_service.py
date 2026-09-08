from __future__ import annotations

from pathlib import Path

from app.core.config import ROOT_DIR
from app.db import database
from app.vision.pipeline import ANALYZER_NAME, ANALYZER_VERSION, analyze_image


class FrameMediaUnavailable(RuntimeError):
    pass


def _frame_path(frame: dict) -> Path:
    candidate = frame.get("local_path") or frame.get("source_url")
    if not candidate or candidate.startswith(("http://", "https://")):
        raise FrameMediaUnavailable(
            "Download this frame first, or analyze a locally uploaded frame."
        )
    path = (ROOT_DIR / candidate).resolve()
    storage_root = (ROOT_DIR / "storage").resolve()
    if storage_root not in path.parents or not path.is_file():
        raise FrameMediaUnavailable("The local frame file is missing from managed storage.")
    return path


def analyze_frame(frame_id: int) -> dict:
    frame = database.get_frame(frame_id)
    if not frame:
        raise LookupError("Frame not found")
    output = analyze_image(_frame_path(frame))
    return database.upsert_frame_analysis(
        {
            "frame_id": frame_id,
            "analyzer_name": ANALYZER_NAME,
            "analyzer_version": ANALYZER_VERSION,
            "results": output["results"],
            "execution_ms": output["execution_ms"],
        }
    )


def get_frame_analyses(frame_id: int) -> list[dict]:
    if not database.get_frame(frame_id):
        raise LookupError("Frame not found")
    return database.list_frame_analyses(frame_id)
