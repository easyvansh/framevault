SCHEMA_SQL = """
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
    source_type TEXT NOT NULL DEFAULT 'filmgrab',
    source_identifier TEXT NOT NULL,
    content_hash TEXT,
    ingestion_status TEXT NOT NULL DEFAULT 'active',
    ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (film_id) REFERENCES films(id) ON DELETE CASCADE,
    UNIQUE (film_id, source_url),
    UNIQUE (film_id, source_type, source_identifier)
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
