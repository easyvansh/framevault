from fastapi import APIRouter, HTTPException

from app.db import database
from app.models.schemas import FrameRecord, SelectFrameRequest
from app.services.analysis_service import (
    FrameMediaUnavailable,
    analyze_frame,
    get_frame_analyses,
)


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


@router.post("/frames/{frame_id}/analysis")
def run_frame_analysis(frame_id: int) -> dict:
    try:
        return analyze_frame(frame_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FrameMediaUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/frames/{frame_id}/analysis")
def list_frame_analysis(frame_id: int) -> list[dict]:
    try:
        return get_frame_analyses(frame_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
