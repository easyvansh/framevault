from fastapi import APIRouter

from app.core.config import APP_NAME


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app": APP_NAME,
    }