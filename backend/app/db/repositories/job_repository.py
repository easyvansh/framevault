from __future__ import annotations

import sqlite3

from app.db.database import get_connection


def record_scrape_success(
    film_id: int,
    image_count: int,
    connection: sqlite3.Connection | None = None,
) -> None:
    owns_connection = connection is None

    if owns_connection:
        connection_context = get_connection()
        connection = connection_context.__enter__()

    try:
        connection.execute(
            """
            INSERT INTO scrape_jobs (
                film_id,
                source_url,
                status,
                image_count
            )
            SELECT
                id,
                filmgrab_url,
                'success',
                ?
            FROM films
            WHERE id = ?
            """,
            (image_count, film_id),
        )

    finally:
        if owns_connection:
            connection_context.__exit__(None, None, None)