from __future__ import annotations

import sqlite3

from app.db.database import get_connection


def film_from_row(row: dict) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "filmgrab_url": row["filmgrab_url"],
        "thumbnail_url": row.get("thumbnail_url"),
        "image_count": row.get("image_count", 0) or 0,
        "downloaded_count": row.get("downloaded_count", 0) or 0,
    }


def upsert_film(
    title: str,
    filmgrab_url: str,
    thumbnail_url: str | None = None,
) -> dict:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO films (title, filmgrab_url, thumbnail_url)
            VALUES (?, ?, ?)
            ON CONFLICT(filmgrab_url) DO UPDATE SET
                title = excluded.title,
                thumbnail_url = COALESCE(
                    excluded.thumbnail_url,
                    films.thumbnail_url
                ),
                updated_at = CURRENT_TIMESTAMP
            """,
            (title, filmgrab_url, thumbnail_url),
        )

        return get_film_by_url(
            filmgrab_url,
            connection=connection,
        )


def get_film_by_url(
    filmgrab_url: str,
    connection: sqlite3.Connection | None = None,
) -> dict:
    owns_connection = connection is None

    if owns_connection:
        connection_context = get_connection()
        connection = connection_context.__enter__()

    try:
        row = connection.execute(
            """
            SELECT
                f.*,
                COUNT(i.id) AS image_count,
                SUM(
                    CASE
                        WHEN i.downloaded = 1 THEN 1
                        ELSE 0
                    END
                ) AS downloaded_count
            FROM films f
            LEFT JOIN images i ON i.film_id = f.id
            WHERE f.filmgrab_url = ?
            GROUP BY f.id
            """,
            (filmgrab_url,),
        ).fetchone()

        if row is None:
            raise LookupError("Film not found")

        return film_from_row(row)

    finally:
        if owns_connection:
            connection_context.__exit__(None, None, None)


def get_film(film_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                f.*,
                COUNT(i.id) AS image_count,
                SUM(
                    CASE
                        WHEN i.downloaded = 1 THEN 1
                        ELSE 0
                    END
                ) AS downloaded_count
            FROM films f
            LEFT JOIN images i ON i.film_id = f.id
            WHERE f.id = ?
            GROUP BY f.id
            """,
            (film_id,),
        ).fetchone()

        return film_from_row(row) if row else None


def list_films() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                f.*,
                COUNT(i.id) AS image_count,
                SUM(
                    CASE
                        WHEN i.downloaded = 1 THEN 1
                        ELSE 0
                    END
                ) AS downloaded_count
            FROM films f
            LEFT JOIN images i ON i.film_id = f.id
            GROUP BY f.id
            ORDER BY f.updated_at DESC
            """
        ).fetchall()

        return [film_from_row(row) for row in rows]