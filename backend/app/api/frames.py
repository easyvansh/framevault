from fastapi import APIRouter, HTTPException

from app.db import database
from app.models.schemas import ImageRecord, SelectImageRequest


router = APIRouter(prefix="/api/images", tags=["frames"])


@router.post("/{image_id}/select", response_model=ImageRecord)
def select_image(
    image_id: int,
    request: SelectImageRequest,
) -> dict:
    image = database.set_image_selected(
        image_id,
        request.selected,
    )

    if not image:
        raise HTTPException(
            status_code=404,
            detail="Image not found",
        )

    return image