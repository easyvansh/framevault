from __future__ import annotations

import sqlite3

from app.db.database import get_connection
from app.db.repositories.job_repository import record_scrape_success


def image_from_row(row: dict) -> dict:
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


def replace_film_images(
    film_id: int,
    images: list[dict],
) -> list[dict]:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM images WHERE film_id = ?",
            (film_id,),
        )

        for image in images:
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
                    image["source_url"],
                    image.get("preview_url"),
                    image.get("width"),
                    image.get("height"),
                    image.get("alt_text"),
                ),
            )

        record_scrape_success(
            film_id,
            len(images),
            connection=connection,
        )

        return list_images_for_film(
            film_id,
            connection=connection,
        )


def list_images_for_film(
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
            image_from_row(row)
            for row in rows
        ]

    finally:
        if owns_connection:
            connection_context.__exit__(None, None, None)


def set_image_selected(
    image_id: int,
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
                image_id,
            ),
        )

        row = connection.execute(
            """
            SELECT *
            FROM images
            WHERE id = ?
            """,
            (image_id,),
        ).fetchone()

        return image_from_row(row) if row else None


def mark_image_downloaded(
    image_id: int,
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
            (local_path, image_id),
        )