from fastapi import APIRouter, HTTPException

from app.db import database
from app.models.schemas import FrameRecord, SelectFrameRequest


router = APIRouter(prefix="/api", tags=["frames"])


def _select_frame(frame_id: int, request: SelectFrameRequest) -> dict:
    frame = database.set_frame_selected(frame_id, request.selected)

    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")

    return frame


@router.post("/frames/{frame_id}/select", response_model=FrameRecord)
def select_frame(
    frame_id: int,
    request: SelectFrameRequest,
) -> dict:
    return _select_frame(frame_id, request)


@router.post("/images/{frame_id}/select", response_model=FrameRecord)
def select_image(frame_id: int, request: SelectFrameRequest) -> dict:
    return _select_frame(frame_id, request)
