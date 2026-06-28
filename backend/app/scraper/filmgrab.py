from __future__ import annotations

import re
import time
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from requests.exceptions import SSLError
from urllib3.exceptions import InsecureRequestWarning
import urllib3


BASE_URL = "https://film-grab.com/"
USER_AGENT = "FrameVault/1.0 (+local offline curator)"
TIMEOUT = 20


class FilmGrabError(RuntimeError):
    pass


def _request(url: str) -> str:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
    except SSLError:
        urllib3.disable_warnings(InsecureRequestWarning)
        response = requests.get(url, headers=headers, timeout=TIMEOUT, verify=False)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def _absolute_url(value: str | None) -> str | None:
    if not value:
        return None
    return urljoin(BASE_URL, value.strip())


def _clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _normalise_image_url(url: str) -> str:
    parsed = urlparse(url)
    query = [(key, value) for key, value in parse_qsl(parsed.query) if key != "bwg"]
    return urlunparse(parsed._replace(query=urlencode(query)))


def _full_size_key(url: str) -> str:
    parsed = urlparse(_normalise_image_url(url))
    path = parsed.path.replace("/thumb/", "/")
    return urlunparse(parsed._replace(path=path, query=""))


def _best_srcset_url(srcset: str | None) -> str | None:
    if not srcset:
        return None
    candidates = []
    for part in srcset.split(","):
        bits = part.strip().split()
        if not bits:
            continue
        url = bits[0]
        width = 0
        if len(bits) > 1 and bits[1].endswith("w"):
            try:
                width = int(bits[1][:-1])
            except ValueError:
                width = 0
        candidates.append((width, url))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _best_image_url(img) -> str | None:
    for attr in ("data-orig-file", "data-large-file", "data-original", "src"):
        url = _absolute_url(img.get(attr))
        if url:
            return url
    return _absolute_url(_best_srcset_url(img.get("srcset")))


def search_filmgrab(query: str) -> list[dict]:
    search = query.strip()
    if not search:
        return []

    html = _request(f"{BASE_URL}?{urlencode({'s': search})}")
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen_urls = set()

    for article in soup.select("article"):
        title_link = article.select_one("h2.entry-title a")
        if not title_link:
            continue
        url = _absolute_url(title_link.get("href"))
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        thumbnail = None
        img = article.select_one(".entry-thumb img") or article.select_one("img")
        if img:
            thumbnail = _best_image_url(img)
        excerpt = article.select_one(".entry-summary")
        results.append(
            {
                "title": _clean_text(title_link.get_text(" ")),
                "url": url,
                "excerpt": _clean_text(excerpt.get_text(" ")) if excerpt else None,
                "thumbnail_url": thumbnail,
            }
        )

    return results


def extract_images_from_film_page(url: str) -> list[dict]:
    html = _request(url)
    soup = BeautifulSoup(html, "html.parser")
    images = []
    seen_urls = set()

    def add_image(source_url: str | None, preview_url: str | None = None, img=None) -> None:
        source_url = _absolute_url(source_url)
        if not source_url:
            return
        if not re.search(r"\.(jpe?g|png|webp)(\?|$)", source_url, re.IGNORECASE):
            return
        normalised = _full_size_key(source_url)
        if normalised in seen_urls:
            return
        seen_urls.add(normalised)
        width = None
        height = None
        alt_text = None
        if img:
            width = _safe_int(img.get("width") or img.get("data-width"))
            height = _safe_int(img.get("height") or img.get("data-height"))
            alt_text = _clean_text(img.get("alt"))
        images.append(
            {
                "source_url": source_url,
                "preview_url": _absolute_url(preview_url) or source_url,
                "width": width,
                "height": height,
                "alt_text": alt_text,
            }
        )

    for link in soup.select("a.bwg-a.bwg_lightbox[href], a.bwg_lightbox[href]"):
        img = link.select_one("img")
        preview = img.get("src") if img else None
        add_image(link.get("href"), preview_url=preview, img=img)

    for img in soup.select("img"):
        add_image(
            img.get("data-orig-file")
            or img.get("data-large-file")
            or _best_srcset_url(img.get("srcset"))
            or img.get("src"),
            preview_url=img.get("src"),
            img=img,
        )

    if not images:
        raise FilmGrabError("No image URLs were found on this FilmGrab page.")

    time.sleep(0.25)
    return images


def _safe_int(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None
