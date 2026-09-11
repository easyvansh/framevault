from __future__ import annotations

from app.db.database import get_connection


def replace_shots(media_asset_id: int, shots: list[dict]) -> list[dict]:
    with get_connection() as connection:
        connection.execute("DELETE FROM shots WHERE media_asset_id = ?", (media_asset_id,))
        connection.executemany(
            """
            INSERT INTO shots (
                media_asset_id, shot_index, start_ms, end_ms,
                keyframe_frame_id, detection_method, threshold
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    media_asset_id,
                    shot["shot_index"],
                    shot["start_ms"],
                    shot["end_ms"],
                    shot.get("keyframe_frame_id"),
                    shot.get("detection_method", "ffmpeg_scene"),
                    shot["threshold"],
                )
                for shot in shots
            ],
        )
        rows = connection.execute(
            "SELECT * FROM shots WHERE media_asset_id = ? ORDER BY shot_index",
            (media_asset_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def list_shots(media_asset_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM shots WHERE media_asset_id = ? ORDER BY shot_index",
            (media_asset_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_shot_for_frame(frame_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM shots WHERE keyframe_frame_id = ?", (frame_id,)).fetchone()
        return dict(row) if row else None
