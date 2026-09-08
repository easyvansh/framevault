from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.db import database
from app.services import analysis_service
from app.vision.pipeline import analyze_image


def test_classical_analysis_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "blue.png"
    Image.new("RGB", (160, 90), (20, 40, 180)).save(path)
    first = analyze_image(path)["results"]
    second = analyze_image(path)["results"]

    assert first == second
    assert first["dimensions"]["aspect_ratio"] == 1.7778
    assert first["color"]["average_rgb"] == [20.0, 40.0, 180.0]
    assert first["color"]["temperature_bias"] < 0
    assert 0 <= first["luminance"]["brightness"] <= 1
    assert 0 <= first["composition"]["symmetry"] <= 1


def test_analysis_api_persists_and_updates_same_version(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    storage = tmp_path / "storage"
    storage.mkdir()
    image_path = storage / "frame.png"
    Image.new("RGB", (32, 18), (128, 128, 128)).save(image_path)
    monkeypatch.setattr(analysis_service, "ROOT_DIR", tmp_path)

    film = database.upsert_film("Analysis", "https://example.com/analysis", None)
    frame = database.replace_film_frames(
        film["id"],
        [{"source_url": "storage/frame.png", "source_type": "upload"}],
    )[0]

    first = client.post(f"/api/frames/{frame['id']}/analysis")
    second = client.post(f"/api/frames/{frame['id']}/analysis")
    listed = client.get(f"/api/frames/{frame['id']}/analysis")

    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert len(listed.json()) == 1
    assert listed.json()[0]["results"]["quality"]["underexposed"] is False


def test_remote_only_frame_returns_actionable_conflict(client: TestClient) -> None:
    film = database.upsert_film("Remote", "https://example.com/remote", None)
    frame = database.replace_film_frames(
        film["id"], [{"source_url": "https://example.com/frame.jpg"}]
    )[0]
    response = client.post(f"/api/frames/{frame['id']}/analysis")
    assert response.status_code == 409
    assert "Download" in response.json()["detail"]
