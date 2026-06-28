# FrameVault

FrameVault is a local cinematography reference engine. Version 1 searches FilmGrab, scrapes still-image metadata from a selected film page, previews the discovered frames, lets frames be selected, and downloads selected or full sets into local folders with JSON metadata.

The project is intentionally built as a non-ML foundation first: reliable scraping, metadata persistence, preview, selection, and offline storage. Version 2 is planned for semantic search and visual analysis.

## Version 1 Features

- Search FilmGrab by film title, director, cinematographer, or keyword.
- Display FilmGrab post results with title, source link, excerpt, and thumbnail.
- Scrape a selected FilmGrab page for still images.
- Preview scraped frames in a responsive curator grid.
- Select and unselect frames before download.
- Download selected frames or all discovered frames.
- Store images locally under organized film folders.
- Write `metadata.json` containing source URLs, local paths, film title, FilmGrab URL, and download time.
- Track films and images in SQLite.
- Avoid uncontrolled duplicate database rows and duplicate downloads.
- Handle empty searches, scrape errors, and download failures with UI messages.

## Tech Stack

Backend:

- Python
- FastAPI
- Requests
- BeautifulSoup
- Pydantic
- SQLite via `sqlite3`
- Local filesystem storage

Frontend:

- React
- Vite
- Tailwind CSS
- Axios

Storage:

- SQLite database for metadata
- Local folders for downloaded image files
- JSON sidecar metadata per downloaded film folder

## Architecture

```text
FrameVault
├── backend
│   ├── app/main.py                 FastAPI routes and app startup
│   ├── app/scraper/filmgrab.py     FilmGrab search and image extraction
│   ├── app/db/database.py          SQLite schema and persistence helpers
│   ├── app/services/download_service.py
│   │                                  Image download and metadata writing
│   └── app/models/schemas.py       API request/response models
├── frontend
│   ├── src/api/client.js           API client with backend fallback
│   ├── src/pages/SearchPage.jsx    Search and scrape entry point
│   ├── src/pages/CuratorPage.jsx   Preview/select/download workflow
│   ├── src/pages/LibraryPage.jsx   Local film/library overview
│   └── src/components              Reusable cards and image grid
├── data                            Local SQLite database, gitignored
└── storage                         Local downloaded images, gitignored
```

## How Version 1 Works

### 1. Search

The frontend calls:

```text
GET /api/search?q=<query>
```

The backend requests FilmGrab search results:

```text
https://film-grab.com/?s=<query>
```

The scraper parses WordPress result cards:

```text
FilmGrab search HTML
    -> article
    -> h2.entry-title a       title + FilmGrab page URL
    -> .entry-summary         film/director/year excerpt
    -> img[data-orig-file]    thumbnail fallback source
```

The response is a list of result objects:

```json
{
  "title": "Blade Runner",
  "url": "https://film-grab.com/2010/06/23/blade-runner/",
  "excerpt": "[Ridley Scott • 1982]",
  "thumbnail_url": "https://film-grab.com/..."
}
```

### 2. Scrape

After a result is selected, the frontend calls:

```text
POST /api/scrape
```

with:

```json
{
  "url": "https://film-grab.com/2010/06/23/blade-runner/",
  "title": "Blade Runner",
  "thumbnail_url": "https://film-grab.com/..."
}
```

The scraper reads the FilmGrab film page and extracts image links. Current FilmGrab pages expose gallery images through BWG Photo Gallery markup:

```text
Film page HTML
    -> a.bwg-a.bwg_lightbox[href]   full image URL
    -> nested img[src]              preview thumbnail
```

Fallback extraction also checks:

```text
img[data-orig-file]
img[data-large-file]
img[srcset]
img[src]
```

The backend deduplicates normalized image URLs, upserts the film, replaces that film's image records, and stores image metadata in SQLite.

### 3. Preview and Select

The curator page calls:

```text
GET /api/films/{film_id}/images
```

The UI renders preview URLs in a grid. Clicking a frame toggles selection:

```text
POST /api/images/{image_id}/select
```

with:

```json
{ "selected": true }
```

### 4. Download

Selected download:

```text
POST /api/download/selected
```

All discovered frames:

```text
POST /api/download/all
```

The download service:

1. Reads the film and image records from SQLite.
2. Creates a safe local film folder name.
3. Downloads source image URLs with a user-agent and timeout.
4. Skips already-downloaded files when possible.
5. Updates image records with local file paths.
6. Writes `metadata.json`.

Example output:

```text
storage/
└── selected/
    └── Blade Runner/
        ├── blade-runner-001.jpg
        └── metadata.json
```

Example metadata:

```json
{
  "film_title": "Blade Runner",
  "filmgrab_url": "https://film-grab.com/2010/06/23/blade-runner/",
  "downloaded_at": "2026-06-28T20:32:39.075865+00:00",
  "selected_only": true,
  "images": [
    {
      "source_url": "https://film-grab.com/wp-content/uploads/photo-gallery/01.jpg",
      "local_path": "storage/selected/Blade Runner/blade-runner-001.jpg",
      "selected": true
    }
  ]
}
```

## API Summary

```text
GET  /health
GET  /api/search?q=<query>
POST /api/scrape
GET  /api/films
GET  /api/films/{film_id}/images
POST /api/images/{image_id}/select
POST /api/download/selected
POST /api/download/all
```

## Run Locally

Create and install the backend environment:

```powershell
cd D:\Projects\2026\FrameVault
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r backend\requirements.txt
```

Install frontend dependencies:

```powershell
cd D:\Projects\2026\FrameVault\frontend
npm.cmd install
```

Start the backend:

```powershell
cd D:\Projects\2026\FrameVault
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --app-dir backend
```

Start the frontend:

```powershell
cd D:\Projects\2026\FrameVault\frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

## Design and Engineering Principles

- Build the local ingestion and curation pipeline before adding ML.
- Keep route handlers thin and place scraping/download logic in separate modules.
- Store source URLs for traceability.
- Preserve metadata for every downloaded frame.
- Use polite scraping behavior: user-agent headers, timeouts, and small delays.
- Avoid hardcoding one film or one page structure.
- Treat FilmGrab markup as unstable and use fallback selectors.
- Keep storage local and transparent.
- Keep Version 1 single-user and offline-first.

## Version 2 Plan

Version 2 will add machine-learning and analysis features on top of the V1 ingestion foundation:

- CLIP/OpenCLIP embeddings for semantic image search.
- Vector search with Qdrant or pgvector.
- Visual similarity search across downloaded frames.
- Color palette extraction.
- Shot-scale and composition classification.
- Scene/location classification.
- Moodboard creation and export.
- Cinematographer/director visual comparison.
- Evaluation reports for search relevance and classifier accuracy.

Version 2 depends on Version 1 because ML indexing needs a reliable local corpus of downloaded images, source URLs, and metadata.
