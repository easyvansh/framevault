from __future__ import annotations

from fastapi.testclient import TestClient

from app.db import database


def seed_frame() -> tuple[dict, dict]:
    film = database.upsert_film(
        "Test Film",
        "https://example.com/test-film",
        None,
    )
    frames = database.replace_film_frames(
        film["id"],
        [{"source_url": "https://example.com/frame-1.jpg"}],
    )
    return film, frames[0]


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_canonical_and_legacy_frame_routes(client: TestClient) -> None:
    film, frame = seed_frame()

    canonical = client.get(f"/api/films/{film['id']}/frames")
    legacy = client.get(f"/api/films/{film['id']}/images")

    assert canonical.status_code == 200
    assert legacy.status_code == 200
    assert canonical.json() == legacy.json()
    assert canonical.json()[0]["id"] == frame["id"]


def test_selection_routes_share_frame_behavior(client: TestClient) -> None:
    _, frame = seed_frame()

    selected = client.post(
        f"/api/frames/{frame['id']}/select",
        json={"selected": True},
    )
    cleared = client.post(
        f"/api/images/{frame['id']}/select",
        json={"selected": False},
    )

    assert selected.status_code == 200
    assert selected.json()["selected"] is True
    assert cleared.status_code == 200
    assert cleared.json()["selected"] is False


def test_missing_frame_returns_404(client: TestClient) -> None:
    response = client.post("/api/frames/999/select", json={"selected": True})
    assert response.status_code == 404
    assert response.json()["detail"] == "Frame not found"
