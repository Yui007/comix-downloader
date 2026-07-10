"""Browser-free Comix API wrapper.

The original upstream implementation used nodriver, page rendering, canvas
extraction, and persisted browser cookies. This replacement uses curl_cffi
plus the static Python secure-module extractor in src.api.secure.
"""
from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urljoin

from curl_cffi import requests

from ..core.models import Chapter, MangaInfo
from .secure import SecurePlan, decrypt_response, extract_plan, signed_token


logger = logging.getLogger(__name__)
SITE = "https://comix.to"
API = f"{SITE}/api/v1"
API_HEADERS = {"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}


@dataclass(frozen=True)
class ChapterPage:
    url: str
    width: int | None = None
    height: int | None = None


class BrowserFreeComix:
    """Immutable secure plan plus manga-page metadata safe for worker reuse."""

    def __init__(self, page_url: str, manga_code: str):
        self.page_url = page_url
        self.manga_code = manga_code
        self._plan: SecurePlan | None = None
        self._detail: dict[str, Any] | None = None
        self._lock = threading.Lock()

    @property
    def plan(self) -> SecurePlan:
        self._ensure_loaded()
        assert self._plan is not None
        return self._plan

    @property
    def detail(self) -> dict[str, Any]:
        self._ensure_loaded()
        assert self._detail is not None
        return self._detail

    def _ensure_loaded(self) -> None:
        if self._plan is not None and self._detail is not None:
            return
        with self._lock:
            if self._plan is not None and self._detail is not None:
                return
            session = requests.Session(impersonate="chrome")
            page = session.get(self.page_url, timeout=30)
            page.raise_for_status()
            initial = _initial_data(page.text)
            detail = _manga_detail(initial, self.manga_code)
            main_url = _main_asset_url(page.url, page.text)
            main = session.get(main_url, timeout=30)
            main.raise_for_status()
            secure_match = re.search(r"(?:\./)?(secure-[A-Za-z0-9._-]+\.js)", main.text)
            if secure_match is None:
                raise RuntimeError("could not find a secure module in the main asset")
            secure = session.get(urljoin(main_url, secure_match.group(1)), timeout=30)
            secure.raise_for_status()
            self._plan = extract_plan(secure.text)
            self._detail = detail

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Make one signed API request; every request receives a fresh TLS session."""
        plan = self.plan
        request_params = dict(params or {})
        request_params[plan.token_parameter] = signed_token(path, request_params, plan)
        response = requests.get(
            f"{API}{path}",
            params=request_params,
            impersonate="chrome",
            headers={**API_HEADERS, "Referer": self.page_url, "Origin": SITE},
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        if "e" in body:
            return decrypt_response(body["e"], plan)
        return body


def _initial_data(html: str) -> dict[str, Any]:
    match = re.search(
        r"<script\b(?=[^>]*\bid=[\"']initial-data[\"'])[^>]*>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        raise RuntimeError("page did not include initial-data")
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as error:
        raise RuntimeError("initial-data was not valid JSON") from error


def _manga_detail(initial: dict[str, Any], manga_code: str) -> dict[str, Any]:
    queries = initial.get("queries", {})
    for value in queries.values():
        if isinstance(value, dict) and value.get("hid") == manga_code:
            return value
    for value in queries.values():
        if isinstance(value, dict) and value.get("id") and value.get("url", "").startswith(f"/title/{manga_code}"):
            return value
    raise RuntimeError(f"could not find manga detail for {manga_code!r} in initial-data")


def _main_asset_url(page_url: str, html: str) -> str:
    scripts = re.findall(r"<script\b[^>]*\bsrc=[\"']([^\"']+\.js)[\"']", html, flags=re.IGNORECASE)
    main_path = next(
        (item for item in scripts if "/main-" in item or item.rsplit("/", 1)[-1].startswith("main-")),
        None,
    )
    if main_path is None:
        raise RuntimeError("could not find a main JavaScript asset")
    return urljoin(page_url, main_path)


class ComixAPI:
    """Compatibility facade used by the retained CLI and PyQt GUI."""

    _clients: dict[str, BrowserFreeComix] = {}
    _clients_lock = threading.Lock()

    @staticmethod
    def extract_manga_code(url: str) -> str:
        match = re.search(r"/title/([a-z0-9]+)(?:[-/]|$)", url, flags=re.IGNORECASE)
        if match is None:
            raise ValueError("expected a comix.to title URL")
        return match.group(1)

    @classmethod
    def _client(cls, manga_code: str) -> BrowserFreeComix:
        with cls._clients_lock:
            client = cls._clients.get(manga_code)
            if client is None:
                client = BrowserFreeComix(f"{SITE}/title/{manga_code}", manga_code)
                cls._clients[manga_code] = client
        client._ensure_loaded()
        return client

    @classmethod
    def get_manga_info(cls, manga_code: str) -> MangaInfo:
        """Fetch manga detail from the server-rendered title page."""
        detail = cls._client(manga_code).detail
        poster = detail.get("poster") if isinstance(detail.get("poster"), dict) else {}
        return MangaInfo(
            manga_id=detail.get("id"),
            hash_id=detail.get("hid"),
            title=detail.get("title", "Unknown"),
            alt_titles=detail.get("altTitles") if isinstance(detail.get("altTitles"), list) else [],
            slug=(detail.get("url") or "").rsplit("/", 1)[-1] or manga_code,
            rank=detail.get("rank"),
            manga_type=detail.get("type"),
            poster_url=poster.get("large") or poster.get("medium"),
            original_language=detail.get("originalLanguage"),
            status=detail.get("status"),
            final_chapter=str(detail.get("finalChapter") or 0),
            latest_chapter=str(detail.get("latestChapter") or 0),
            start_date=detail.get("startDate"),
            end_date=detail.get("endDate"),
            rated_avg=detail.get("ratedAvg"),
            rated_count=detail.get("ratedCount"),
            follows_total=detail.get("followsTotal"),
            is_nsfw=detail.get("contentRating") == "nsfw",
            year=detail.get("year"),
            genres=detail.get("genres") if isinstance(detail.get("genres"), list) else [],
            description=detail.get("synopsis", ""),
        )

    @classmethod
    def get_all_chapters(cls, manga_code: str) -> list[Chapter]:
        """Fetch chapter pages directly from the signed API, without DOM scraping."""
        client = cls._client(manga_code)
        chapters: list[Chapter] = []
        seen: set[int] = set()
        page = 1
        while True:
            result = client.get(f"/manga/{manga_code}/chapters", {"page": page})
            items = result.get("items", []) if isinstance(result, dict) else []
            for item in items:
                chapter_id = item.get("id")
                if not isinstance(chapter_id, int) or chapter_id in seen:
                    continue
                seen.add(chapter_id)
                group = item.get("group") if isinstance(item.get("group"), dict) else {}
                chapters.append(
                    Chapter(
                        chapter_id=chapter_id,
                        number=str(item.get("number", "?")),
                        title=item.get("name") or None,
                        volume=str(item["volume"]) if item.get("volume") else None,
                        votes=item.get("votes"),
                        group_name=group.get("name") or ("Official" if item.get("isOfficial") else "Unknown"),
                        pages_count=0,
                    )
                )
            meta = result.get("meta", {}) if isinstance(result, dict) else {}
            last_page = meta.get("lastPage") or meta.get("last_page") or page
            if not items or page >= int(last_page):
                break
            page += 1
        chapters.sort(key=lambda item: (float(item.number) if _is_number(item.number) else float("inf"), item.chapter_id))
        return chapters

    @classmethod
    def get_chapter_pages(cls, chapter_id: int, manga_slug: str, chapter_number: str) -> list[ChapterPage]:
        manga_code = manga_slug.split("-", 1)[0]
        result = cls._client(manga_code).get(f"/chapters/{chapter_id}")
        pages = result.get("pages", {}).get("items", []) if isinstance(result, dict) else []
        return [
            ChapterPage(item["url"], item.get("width"), item.get("height"))
            for item in pages
            if isinstance(item, dict) and item.get("url")
        ]

    @classmethod
    def get_chapter_images(
        cls,
        chapter_id: int,
        manga_slug: str | None = None,
        chapter_number: str | None = None,
    ) -> list[str]:
        """Return direct WebP page URLs for the retained downloader interface."""
        if not manga_slug or chapter_number is None:
            raise ValueError("manga_slug and chapter_number are required by the browser-free API")
        return [page.url for page in cls.get_chapter_pages(chapter_id, manga_slug, str(chapter_number))]


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False
