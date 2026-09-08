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
        _migrate_legacy_schema(connection)


def _migrate_legacy_schema(connection: sqlite3.Connection) -> None:
    """Apply safe additive migrations to databases created before V2."""
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(images)").fetchall()
    }
    additions = {
        "source_type": "TEXT NOT NULL DEFAULT 'filmgrab'",
        "source_identifier": "TEXT",
        "content_hash": "TEXT",
        "ingestion_status": "TEXT NOT NULL DEFAULT 'active'",
        "ingested_at": "TEXT",
        "media_asset_id": "INTEGER",
    }

    for name, definition in additions.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE images ADD COLUMN {name} {definition}")

    connection.execute(
        """
        UPDATE images
        SET
            source_identifier = COALESCE(source_identifier, source_url),
            ingested_at = COALESCE(ingested_at, created_at)
        WHERE source_identifier IS NULL OR ingested_at IS NULL
        """
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_images_source_identity
        ON images (film_id, source_type, source_identifier)
        """
    )

    asset_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(media_assets)").fetchall()
    }
    asset_additions = {
        "width": "INTEGER",
        "height": "INTEGER",
        "duration_ms": "INTEGER",
        "frame_rate": "REAL",
        "metadata_json": "TEXT",
    }
    for name, definition in asset_additions.items():
        if name not in asset_columns:
            connection.execute(
                f"ALTER TABLE media_assets ADD COLUMN {name} {definition}"
            )


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
    get_frame,
    list_frames_for_film,
    list_images_for_film,
    mark_frame_downloaded,
    mark_image_downloaded,
    replace_film_frames,
    replace_film_images,
    set_frame_selected,
    set_image_selected,
)
from app.db.repositories.analysis_repository import (  # noqa: E402
    list_frame_analyses,
    upsert_frame_analysis,
)
from app.db.repositories.media_asset_repository import (  # noqa: E402
    get_media_asset,
    upsert_media_asset,
)
