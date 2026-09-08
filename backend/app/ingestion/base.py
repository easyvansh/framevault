from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class FrameCandidate:
    source_type: str
    source_identifier: str
    source_url: str
    preview_url: str | None = None
    width: int | None = None
    height: int | None = None
    alt_text: str | None = None
    content_hash: str | None = None
    media_asset_id: int | None = None
    ingestion_status: str = "active"

    def to_record(self) -> dict:
        return asdict(self)
