from __future__ import annotations

import sqlite3

from app.db.database import get_connection
from app.db.repositories.job_repository import record_scrape_success


def frame_from_row(row: dict) -> dict:
    return {
        "id": row["id"],
        "film_id": row["film_id"],
        "source_url": row["source_url"],
        "preview_url": row.get("preview_url"),
        "local_path": row.get("local_path"),
        "selected": bool(row.get("selected")),
        "downloaded": bool(row.get("downloaded")),
        "width": row.get("width"),
        "height": row.get("height"),
        "alt_text": row.get("alt_text"),
    }


def replace_film_frames(
    film_id: int,
    frames: list[dict],
) -> list[dict]:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM images WHERE film_id = ?",
            (film_id,),
        )

        for frame in frames:
            connection.execute(
                """
                INSERT INTO images (
                    film_id,
                    source_url,
                    preview_url,
                    width,
                    height,
                    alt_text
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(film_id, source_url) DO UPDATE SET
                    preview_url = COALESCE(
                        excluded.preview_url,
                        images.preview_url
                    ),
                    width = COALESCE(
                        excluded.width,
                        images.width
                    ),
                    height = COALESCE(
                        excluded.height,
                        images.height
                    ),
                    alt_text = COALESCE(
                        excluded.alt_text,
                        images.alt_text
                    ),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    film_id,
                    frame["source_url"],
                    frame.get("preview_url"),
                    frame.get("width"),
                    frame.get("height"),
                    frame.get("alt_text"),
                ),
            )

        record_scrape_success(
            film_id,
            len(frames),
            connection=connection,
        )

        return list_frames_for_film(
            film_id,
            connection=connection,
        )


def list_frames_for_film(
    film_id: int,
    selected_only: bool = False,
    connection: sqlite3.Connection | None = None,
) -> list[dict]:
    owns_connection = connection is None

    if owns_connection:
        connection_context = get_connection()
        connection = connection_context.__enter__()

    try:
        where = "WHERE film_id = ?"
        params: list[int] = [film_id]

        if selected_only:
            where += " AND selected = 1"

        rows = connection.execute(
            f"""
            SELECT *
            FROM images
            {where}
            ORDER BY id ASC
            """,
            params,
        ).fetchall()

        return [
            frame_from_row(row)
            for row in rows
        ]

    finally:
        if owns_connection:
            connection_context.__exit__(None, None, None)


def set_frame_selected(
    frame_id: int,
    selected: bool,
) -> dict | None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE images
            SET
                selected = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                1 if selected else 0,
                frame_id,
            ),
        )

        row = connection.execute(
            """
            SELECT *
            FROM images
            WHERE id = ?
            """,
            (frame_id,),
        ).fetchone()

        return frame_from_row(row) if row else None


def mark_frame_downloaded(
    frame_id: int,
    local_path: str,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE images
            SET
                downloaded = 1,
                local_path = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (local_path, frame_id),
        )


# Compatibility aliases for callers that still use the V1 image terminology.
image_from_row = frame_from_row
list_images_for_film = list_frames_for_film
set_image_selected = set_frame_selected
mark_image_downloaded = mark_frame_downloaded
replace_film_images = replace_film_frames
