from __future__ import annotations

import sqlite3
from pathlib import Path

from app.db import database


def test_legacy_database_is_migrated_without_losing_frames(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "legacy.sqlite"
    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE films (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            filmgrab_url TEXT NOT NULL UNIQUE,
            thumbnail_url TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE images (
            id INTEGER PRIMARY KEY,
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
            UNIQUE (film_id, source_url)
        );
        INSERT INTO films (id, title, filmgrab_url)
        VALUES (1, 'Legacy', 'https://example.com/legacy');
        INSERT INTO images (id, film_id, source_url, selected)
        VALUES (7, 1, 'https://example.com/legacy.jpg', 1);
        """
    )
    connection.commit()
    connection.close()

    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.init_db()

    frame = database.list_frames_for_film(1)[0]
    assert frame["id"] == 7
    assert frame["selected"] is True
    assert frame["source_type"] == "filmgrab"
    assert frame["source_identifier"] == frame["source_url"]
