from __future__ import annotations

import json

from app.db.database import get_connection


def _asset_from_row(row: dict) -> dict:
    return dict(row)


def upsert_media_asset(asset: dict) -> dict:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO media_assets (
                media_type, original_name, mime_type, file_size, checksum,
                managed_path, source_type, status, width, height,
                duration_ms, frame_rate, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_type, checksum) DO UPDATE SET
                original_name = excluded.original_name,
                mime_type = excluded.mime_type,
                file_size = excluded.file_size,
                managed_path = excluded.managed_path,
                status = excluded.status,
                width = excluded.width,
                height = excluded.height,
                duration_ms = excluded.duration_ms,
                frame_rate = excluded.frame_rate,
                metadata_json = excluded.metadata_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                asset["media_type"],
                asset["original_name"],
                asset["mime_type"],
                asset["file_size"],
                asset["checksum"],
                asset["managed_path"],
                asset.get("source_type", "upload"),
                asset.get("status", "ready"),
                asset.get("width"),
                asset.get("height"),
                asset.get("duration_ms"),
                asset.get("frame_rate"),
                json.dumps(asset.get("metadata", {})),
            ),
        )
        row = connection.execute(
            "SELECT * FROM media_assets WHERE source_type = ? AND checksum = ?",
            (asset.get("source_type", "upload"), asset["checksum"]),
        ).fetchone()
        return _asset_from_row(row)


def get_media_asset(asset_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM media_assets WHERE id = ?",
            (asset_id,),
        ).fetchone()
        return _asset_from_row(row) if row else None
