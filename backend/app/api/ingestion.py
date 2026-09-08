from fastapi import APIRouter, HTTPException, Query

from app.db import database
from app.models.schemas import (
    DownloadRequest,
    DownloadResponse,
    FilmResult,
    ScrapeRequest,
    ScrapeResponse,
)
from app.scraper.filmgrab import (
    FilmGrabError,
    extract_images_from_film_page,
    search_filmgrab,
)
from app.services.download_service import download_images_for_film


router = APIRouter(prefix="/api", tags=["ingestion"])


@router.get("/search", response_model=list[FilmResult])
def search(q: str = Query(..., min_length=1)) -> list[dict]:
    try:
        return search_filmgrab(q)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"FilmGrab search failed: {exc}",
        ) from exc


@router.post("/scrape", response_model=ScrapeResponse)
def scrape(request: ScrapeRequest) -> dict:
    try:
        film = database.upsert_film(
            request.title,
            str(request.url),
            request.thumbnail_url,
        )

        images = extract_images_from_film_page(
            str(request.url)
        )

        image_records = database.replace_film_images(
            film["id"],
            images,
        )

        film = database.get_film(film["id"])

        return {
            "film": film,
            "images": image_records,
        }

    except FilmGrabError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"FilmGrab scrape failed: {exc}",
        ) from exc


@router.post(
    "/download/selected",
    response_model=DownloadResponse,
)
def download_selected(request: DownloadRequest) -> dict:
    try:
        return download_images_for_film(
            request.film_id,
            selected_only=True,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post(
    "/download/all",
    response_model=DownloadResponse,
)
def download_all(request: DownloadRequest) -> dict:
    try:
        return download_images_for_film(
            request.film_id,
            selected_only=False,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc