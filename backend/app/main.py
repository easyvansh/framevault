from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.db import database
from app.models.schemas import (
    DownloadRequest,
    DownloadResponse,
    FilmRecord,
    FilmResult,
    ImageRecord,
    ScrapeRequest,
    ScrapeResponse,
    SelectImageRequest,
)
from app.scraper.filmgrab import FilmGrabError, extract_images_from_film_page, search_filmgrab
from app.services.download_service import download_images_for_film


app = FastAPI(title="FrameVault", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    database.init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": "FrameVault"}


@app.get("/api/search", response_model=list[FilmResult])
def search(q: str = Query(..., min_length=1)) -> list[dict]:
    try:
        return search_filmgrab(q)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"FilmGrab search failed: {exc}") from exc


@app.post("/api/scrape", response_model=ScrapeResponse)
def scrape(request: ScrapeRequest) -> dict:
    try:
        film = database.upsert_film(request.title, str(request.url), request.thumbnail_url)
        images = extract_images_from_film_page(str(request.url))
        image_records = database.replace_film_images(film["id"], images)
        film = database.get_film(film["id"])
        return {"film": film, "images": image_records}
    except FilmGrabError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"FilmGrab scrape failed: {exc}") from exc


@app.get("/api/films", response_model=list[FilmRecord])
def films() -> list[dict]:
    return database.list_films()


@app.get("/api/films/{film_id}/images", response_model=list[ImageRecord])
def film_images(film_id: int) -> list[dict]:
    if not database.get_film(film_id):
        raise HTTPException(status_code=404, detail="Film not found")
    return database.list_images_for_film(film_id)


@app.post("/api/images/{image_id}/select", response_model=ImageRecord)
def select_image(image_id: int, request: SelectImageRequest) -> dict:
    image = database.set_image_selected(image_id, request.selected)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@app.post("/api/download/selected", response_model=DownloadResponse)
def download_selected(request: DownloadRequest) -> dict:
    try:
        return download_images_for_film(request.film_id, selected_only=True)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/download/all", response_model=DownloadResponse)
def download_all(request: DownloadRequest) -> dict:
    try:
        return download_images_for_film(request.film_id, selected_only=False)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
