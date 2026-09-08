from fastapi import APIRouter, File, HTTPException, Query, UploadFile

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
from app.ingestion.images import InvalidImageUpload, ingest_uploaded_image
from app.ingestion.filmgrab import filmgrab_candidates
from app.ingestion.video import (
    InvalidVideoUpload,
    VideoToolUnavailable,
    ingest_uploaded_video,
)


router = APIRouter(prefix="/api", tags=["ingestion"])


@router.post("/ingestion/images")
def upload_images(files: list[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(status_code=422, detail="At least one image is required.")

    try:
        items = [ingest_uploaded_image(upload) for upload in files]
    except InvalidImageUpload as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "assets": [item["asset"] for item in items],
        "frames": [item["frame"] for item in items],
    }


@router.post("/ingestion/videos")
def upload_video(file: UploadFile = File(...)) -> dict:
    try:
        return {"asset": ingest_uploaded_video(file)}
    except InvalidVideoUpload as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except VideoToolUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


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

        frames = [
            candidate.to_record()
            for candidate in filmgrab_candidates(
                extract_images_from_film_page(str(request.url))
            )
        ]

        frame_records = database.replace_film_frames(
            film["id"],
            frames,
        )

        film = database.get_film(film["id"])

        return {
            "film": film,
            "images": frame_records,
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
