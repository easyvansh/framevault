from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.db.schema import SCHEMA_SQL


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "framevault.sqlite"


def dict_factory(
    cursor: sqlite3.Cursor,
    row: tuple,
) -> dict:
    return {
        column[0]: row[index]
        for index, column in enumerate(cursor.description)
    }


@contextmanager
def get_connection():
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

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
        connection.executescript(SCHEMA_SQL)


# Compatibility exports.
#
# The rest of FrameVault currently imports persistence functions from
# app.db.database. Re-exporting them here lets us introduce repositories
# without changing every caller in the same commit.
from app.db.repositories.film_repository import (  # noqa: E402
    get_film,
    get_film_by_url,
    list_films,
    upsert_film,
)
from app.db.repositories.frame_repository import (  # noqa: E402
    list_frames_for_film,
    list_images_for_film,
    mark_frame_downloaded,
    mark_image_downloaded,
    replace_film_frames,
    replace_film_images,
    set_frame_selected,
    set_image_selected,
)
