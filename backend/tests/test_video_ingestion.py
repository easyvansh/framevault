from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.ingestion import video


def test_video_endpoint_reports_missing_ffprobe(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(video.shutil, "which", lambda _: None)
    response = client.post(
        "/api/ingestion/videos",
        files={"file": ("clip.mp4", b"video", "video/mp4")},
    )
    assert response.status_code == 503
    assert "FFprobe" in response.json()["detail"]


def test_video_upload_is_probed_and_deduplicated(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(video, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(video, "STORAGE_DIR", tmp_path / "storage" / "uploads" / "videos")
    monkeypatch.setattr(video.shutil, "which", lambda _: "ffprobe")
    probe_payload = {
        "streams": [{
            "codec_type": "video",
            "width": 1920,
            "height": 1080,
            "duration": "2.5",
            "avg_frame_rate": "24/1",
        }],
        "format": {"duration": "2.5"},
    }
    monkeypatch.setattr(
        video.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout=json.dumps(probe_payload), stderr=""
        ),
    )

    first = client.post(
        "/api/ingestion/videos",
        files={"file": ("clip.mp4", b"video-bytes", "video/mp4")},
    )
    second = client.post(
        "/api/ingestion/videos",
        files={"file": ("copy.mp4", b"video-bytes", "video/mp4")},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    asset = first.json()["asset"]
    assert asset["width"] == 1920
    assert asset["duration_ms"] == 2500
    assert asset["frame_rate"] == 24.0
    assert second.json()["asset"]["id"] == asset["id"]
