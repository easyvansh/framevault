from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.ingestion import images as image_ingestion


def image_bytes(format_name: str = "PNG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (16, 9), color=(20, 40, 80)).save(buffer, format=format_name)
    return buffer.getvalue()


def use_temporary_storage(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(image_ingestion, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        image_ingestion,
        "STORAGE_DIR",
        tmp_path / "storage" / "uploads" / "images",
    )


def test_upload_image_creates_asset_and_frame(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    use_temporary_storage(tmp_path, monkeypatch)

    response = client.post(
        "/api/ingestion/images",
        files=[("files", ("../portrait.png", image_bytes(), "image/png"))],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["assets"][0]["original_name"] == "portrait.png"
    assert payload["assets"][0]["mime_type"] == "image/png"
    assert payload["frames"][0]["width"] == 16
    assert payload["frames"][0]["height"] == 9
    assert payload["frames"][0]["source_type"] == "upload"
    assert (tmp_path / payload["assets"][0]["managed_path"]).exists()


def test_duplicate_upload_reuses_asset_and_frame(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    use_temporary_storage(tmp_path, monkeypatch)
    content = image_bytes("JPEG")

    first = client.post(
        "/api/ingestion/images",
        files=[("files", ("one.jpg", content, "image/jpeg"))],
    ).json()
    second = client.post(
        "/api/ingestion/images",
        files=[("files", ("renamed.jpg", content, "image/jpeg"))],
    ).json()

    assert second["assets"][0]["id"] == first["assets"][0]["id"]
    assert second["frames"][0]["id"] == first["frames"][0]["id"]


def test_invalid_and_empty_uploads_are_rejected(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    use_temporary_storage(tmp_path, monkeypatch)

    invalid = client.post(
        "/api/ingestion/images",
        files=[("files", ("fake.png", b"not an image", "image/png"))],
    )
    empty = client.post(
        "/api/ingestion/images",
        files=[("files", ("empty.png", b"", "image/png"))],
    )

    assert invalid.status_code == 422
    assert empty.status_code == 422
