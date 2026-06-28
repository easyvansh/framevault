from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from requests.exceptions import SSLError
from urllib3.exceptions import InsecureRequestWarning
import urllib3
from slugify import slugify

from app.db import database
from app.scraper.filmgrab import USER_AGENT


ROOT_DIR = Path(__file__).resolve().parents[3]
STORAGE_DIR = ROOT_DIR / "storage"


def _film_dir_name(film_title: str) -> str:
    return slugify(film_title, separator=" ", lowercase=False) or "Untitled Film"


def _extension_from_url(source_url: str) -> str:
    path = unquote(urlparse(source_url).path)
    suffix = Path(path).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def download_image(source_url: str, film_title: str, selected: bool) -> dict:
    folder_type = "selected" if selected else "scraped"
    target_dir = STORAGE_DIR / folder_type / _film_dir_name(film_title)
    target_dir.mkdir(parents=True, exist_ok=True)

    index = len([item for item in target_dir.iterdir() if item.is_file() and item.name != "metadata.json"]) + 1
    filename = f"{slugify(film_title) or 'framevault'}-{index:03d}{_extension_from_url(source_url)}"
    target_path = target_dir / filename

    if target_path.exists():
        return {"local_path": _relative_path(target_path), "skipped": True}

    headers = {"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/apng,image/*,*/*"}
    try:
        response = requests.get(source_url, headers=headers, timeout=30, stream=True)
    except SSLError:
        urllib3.disable_warnings(InsecureRequestWarning)
        response = requests.get(source_url, headers=headers, timeout=30, stream=True, verify=False)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "image" not in content_type.lower():
        raise RuntimeError(f"URL did not return an image: {source_url}")

    with target_path.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 128):
            if chunk:
                file.write(chunk)

    time.sleep(0.2)
    return {"local_path": _relative_path(target_path), "skipped": False}


def download_images_for_film(film_id: int, selected_only: bool) -> dict:
    film = database.get_film(film_id)
    if not film:
        raise LookupError("Film not found")

    images = database.list_images_for_film(film_id, selected_only=selected_only)
    destination_kind = "selected" if selected_only else "scraped"
    destination = STORAGE_DIR / destination_kind / _film_dir_name(film["title"])
    destination.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed = 0
    errors = []
    metadata_images = []

    for image in images:
        try:
            existing_path = image.get("local_path")
            if image.get("downloaded") and existing_path and (ROOT_DIR / existing_path).exists():
                result = {"local_path": existing_path, "skipped": True}
            else:
                result = download_image(image["source_url"], film["title"], selected=selected_only)
                database.mark_image_downloaded(image["id"], result["local_path"])
            skipped += 1 if result["skipped"] else 0
            downloaded += 0 if result["skipped"] else 1
            metadata_images.append(
                {
                    "source_url": image["source_url"],
                    "local_path": result["local_path"],
                    "selected": bool(image.get("selected")),
                }
            )
        except Exception as exc:
            failed += 1
            errors.append(f"{image['source_url']}: {exc}")

    metadata_path = destination / "metadata.json"
    metadata = {
        "film_title": film["title"],
        "filmgrab_url": film["filmgrab_url"],
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "selected_only": selected_only,
        "images": metadata_images,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return {
        "film_id": film_id,
        "downloaded": downloaded,
        "skipped": skipped,
        "failed": failed,
        "destination": _relative_path(destination),
        "metadata_path": _relative_path(metadata_path),
        "errors": errors,
    }
