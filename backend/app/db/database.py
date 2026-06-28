from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "framevault.sqlite"


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {column[0]: row[index] for index, column in enumerate(cursor.description)}


@contextmanager
def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = dict_factory
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS films (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filmgrab_url TEXT NOT NULL UNIQUE,
                thumbnail_url TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                film_id INTEGER NOT NULL,
                source_url TEXT NOT NULL,
                preview_url TEXT,
                local_path TEXT,
                selected INTEGER NOT NULL DEFAULT 0,
                downloaded INTEGER NOT NULL DEFAULT 0,
                width INTEGER,
                height INTEGER,
                alt_text TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (film_id) REFERENCES films(id) ON DELETE CASCADE,
                UNIQUE (film_id, source_url)
            );

            CREATE TABLE IF NOT EXISTS scrape_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                film_id INTEGER,
                source_url TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                image_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (film_id) REFERENCES films(id) ON DELETE SET NULL
            );
            """
        )


def film_from_row(row: dict) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "filmgrab_url": row["filmgrab_url"],
        "thumbnail_url": row.get("thumbnail_url"),
        "image_count": row.get("image_count", 0) or 0,
        "downloaded_count": row.get("downloaded_count", 0) or 0,
    }


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


def upsert_film(title: str, filmgrab_url: str, thumbnail_url: str | None = None) -> dict:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO films (title, filmgrab_url, thumbnail_url)
            VALUES (?, ?, ?)
            ON CONFLICT(filmgrab_url) DO UPDATE SET
                title = excluded.title,
                thumbnail_url = COALESCE(excluded.thumbnail_url, films.thumbnail_url),
                updated_at = CURRENT_TIMESTAMP
            """,
            (title, filmgrab_url, thumbnail_url),
        )
        return get_film_by_url(filmgrab_url, connection=connection)


def get_film_by_url(filmgrab_url: str, connection: sqlite3.Connection | None = None) -> dict:
    owns_connection = connection is None
    if owns_connection:
        connection_context = get_connection()
        connection = connection_context.__enter__()
    try:
        row = connection.execute(
            """
            SELECT f.*,
                COUNT(i.id) AS image_count,
                SUM(CASE WHEN i.downloaded = 1 THEN 1 ELSE 0 END) AS downloaded_count
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
            SELECT f.*,
                COUNT(i.id) AS image_count,
                SUM(CASE WHEN i.downloaded = 1 THEN 1 ELSE 0 END) AS downloaded_count
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
            SELECT f.*,
                COUNT(i.id) AS image_count,
                SUM(CASE WHEN i.downloaded = 1 THEN 1 ELSE 0 END) AS downloaded_count
            FROM films f
            LEFT JOIN images i ON i.film_id = f.id
            GROUP BY f.id
            ORDER BY f.updated_at DESC
            """
        ).fetchall()
        return [film_from_row(row) for row in rows]


def replace_film_images(film_id: int, images: list[dict]) -> list[dict]:
    with get_connection() as connection:
        connection.execute("DELETE FROM images WHERE film_id = ?", (film_id,))
        for image in images:
            connection.execute(
                """
                INSERT INTO images (film_id, source_url, preview_url, width, height, alt_text)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(film_id, source_url) DO UPDATE SET
                    preview_url = COALESCE(excluded.preview_url, images.preview_url),
                    width = COALESCE(excluded.width, images.width),
                    height = COALESCE(excluded.height, images.height),
                    alt_text = COALESCE(excluded.alt_text, images.alt_text),
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
        connection.execute(
            """
            INSERT INTO scrape_jobs (film_id, source_url, status, image_count)
            SELECT id, filmgrab_url, 'success', ? FROM films WHERE id = ?
            """,
            (len(images), film_id),
        )
        return list_images_for_film(film_id, connection=connection)


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
            f"SELECT * FROM images {where} ORDER BY id ASC",
            params,
        ).fetchall()
        return [image_from_row(row) for row in rows]
    finally:
        if owns_connection:
            connection_context.__exit__(None, None, None)


def set_image_selected(image_id: int, selected: bool) -> dict | None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE images SET selected = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (1 if selected else 0, image_id),
        )
        row = connection.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
        return image_from_row(row) if row else None


def mark_image_downloaded(image_id: int, local_path: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE images
            SET downloaded = 1, local_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (local_path, image_id),
        )
