from pydantic import BaseModel, HttpUrl


class FilmResult(BaseModel):
    title: str
    url: str
    excerpt: str | None = None
    thumbnail_url: str | None = None


class ImageRecord(BaseModel):
    id: int
    film_id: int
    source_url: str
    preview_url: str | None = None
    local_path: str | None = None
    selected: bool = False
    downloaded: bool = False
    width: int | None = None
    height: int | None = None
    alt_text: str | None = None


class FilmRecord(BaseModel):
    id: int
    title: str
    filmgrab_url: str
    thumbnail_url: str | None = None
    image_count: int = 0
    downloaded_count: int = 0


class ScrapeRequest(BaseModel):
    url: HttpUrl
    title: str
    thumbnail_url: str | None = None


class ScrapeResponse(BaseModel):
    film: FilmRecord
    images: list[ImageRecord]


class SelectImageRequest(BaseModel):
    selected: bool


class DownloadRequest(BaseModel):
    film_id: int


class DownloadResponse(BaseModel):
    film_id: int
    downloaded: int
    skipped: int
    failed: int
    destination: str
    metadata_path: str | None = None
    errors: list[str] = []
