from fastapi import APIRouter, HTTPException

from app.db import database
from app.models.schemas import FrameRecord, SelectFrameRequest
from app.services.analysis_service import (
    FrameMediaUnavailable,
    analyze_frame,
    get_frame_analyses,
)


router = APIRouter(prefix="/api", tags=["frames"])


@router.get("/frames/{frame_id}", response_model=FrameRecord)
def get_frame(frame_id: int) -> dict:
    frame = database.get_frame(frame_id)
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")
    return frame


@router.get("/frames/{frame_id}/details")
def get_frame_details(frame_id: int) -> dict:
    frame = database.get_frame(frame_id)
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")
    return {"frame": frame, "film": database.get_film(frame["film_id"]), "media_asset": database.get_media_asset(frame["media_asset_id"]) if frame.get("media_asset_id") else None, "shot": database.get_shot_for_frame(frame_id), "analyses": database.list_frame_analyses(frame_id)}


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
