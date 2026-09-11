from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from PIL import Image

from app.db import database
from app.services import shot_service


def test_shot_extraction_persists_boundaries_and_keyframes(
    client: TestClient, tmp_path: Path, monkeypatch
) -> None:
    video_path = tmp_path / "storage" / "clip.mp4"
    video_path.parent.mkdir(parents=True)
    video_path.write_bytes(b"video")
    asset = database.upsert_media_asset({
        "media_type": "video", "original_name": "clip.mp4", "mime_type": "video/mp4",
        "file_size": 5, "checksum": "abc123", "managed_path": "storage/clip.mp4",
        "source_type": "upload", "duration_ms": 10_000,
    })
    monkeypatch.setattr(shot_service, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(shot_service, "KEYFRAME_DIR", tmp_path / "storage" / "keyframes")
    monkeypatch.setattr(shot_service.shutil, "which", lambda _: "ffmpeg")

    def fake_run(command, **_kwargs):
        if "null" in command:
            return SimpleNamespace(returncode=0, stdout="", stderr="pts_time:3.0 pts_time:7.5")
        output = Path(command[-1])
        output.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (320, 180), (40, 80, 120)).save(output)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(shot_service.subprocess, "run", fake_run)
    response = client.post(f"/api/media-assets/{asset['id']}/shots?threshold=0.4")

    assert response.status_code == 200
    shots = response.json()["shots"]
    assert [(shot["start_ms"], shot["end_ms"]) for shot in shots] == [
        (0, 3000), (3000, 7500), (7500, 10000)
    ]
    assert all(shot["keyframe_frame_id"] for shot in shots)
    assert client.get(f"/api/media-assets/{asset['id']}/shots").json()["shots"] == shots


def test_shot_extraction_requires_video_asset(client: TestClient) -> None:
    response = client.post("/api/media-assets/999/shots")
    assert response.status_code == 404
