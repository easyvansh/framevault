from fastapi import APIRouter, HTTPException

from app.db import database
from app.models.schemas import FilmRecord, ImageRecord


router = APIRouter(prefix="/api/films", tags=["films"])


@router.get("", response_model=list[FilmRecord])
def list_films() -> list[dict]:
    return database.list_films()


@router.get("/{film_id}/images", response_model=list[ImageRecord])
def list_film_images(film_id: int) -> list[dict]:
    if not database.get_film(film_id):
        raise HTTPException(status_code=404, detail="Film not found")

    return database.list_images_for_film(film_id)