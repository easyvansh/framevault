from __future__ import annotations

from app.ingestion.base import FrameCandidate


def filmgrab_candidates(frames: list[dict]) -> list[FrameCandidate]:
    """Translate scraper output into the common ingestion contract."""
    return [
        FrameCandidate(
            source_type="filmgrab",
            source_identifier=frame.get("source_identifier", frame["source_url"]),
            source_url=frame["source_url"],
            preview_url=frame.get("preview_url"),
            width=frame.get("width"),
            height=frame.get("height"),
            alt_text=frame.get("alt_text"),
        )
        for frame in frames
    ]
