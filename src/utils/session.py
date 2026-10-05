"""Thread-local HTTP session management.

``requests.Session`` owns mutable connection-pool and cookie state and is not a
safe application-wide singleton when many chapter workers use it at once.  The
manager below keeps one bounded pool per worker and can discard a poisoned pool
after a TLS/connection failure.
"""

from __future__ import annotations

from urllib.parse import urlparse
import threading
from typing import Any

import requests

from .comix_session import get_comix_credentials
from .logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Create bounded, disposable sessions for the calling thread."""

    def __init__(self, pool_size: int = 8):
        self.pool_size = max(1, int(pool_size))
        self._local = threading.local()

    @staticmethod
    def _headers() -> dict[str, str]:
        credentials = get_comix_credentials()
        return {
            "User-Agent": credentials.user_agent or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
        }

    def _new_session(self) -> requests.Session:
        from requests.adapters import HTTPAdapter

        session = requests.Session()
        session.headers.update(self._headers())
        adapter = HTTPAdapter(
            pool_connections=self.pool_size,
            pool_maxsize=self.pool_size,
            max_retries=0,
            pool_block=True,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        self._local.session = session
        return session

    def _session(self) -> requests.Session:
        session = getattr(self._local, "session", None)
        if session is None:
            return self._new_session()
        return session

    @property
    def session(self) -> requests.Session:
        """Backward-compatible access to the calling thread's session."""
        return self._session()

    def reset(self) -> None:
        """Close the current worker's pool after a transport failure."""
        session = getattr(self._local, "session", None)
        if session is not None:
            try:
                session.close()
            finally:
                self._local.session = None

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Execute one request; retry policy belongs to the downloader."""
        kwargs.pop("force_flare", None)
        session = self._session()
        credentials = get_comix_credentials()
        if credentials.user_agent:
            session.headers["User-Agent"] = credentials.user_agent

        # Browser cookies are restricted to Comix domains.  In particular, do
        # not leak them to the independent image CDN hosts.
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if credentials.cookie_header and (host == "comix.to" or host.endswith(".comix.to")):
            headers = dict(kwargs.get("headers") or {})
            headers.setdefault("Cookie", credentials.cookie_header)
            kwargs["headers"] = headers

        _h = dict(kwargs.get("headers") or {})
        if host == "comix.to" or host.endswith(".comix.to"):
            _h.setdefault("Referer", "https://comix.to/")
        kwargs["headers"] = _h
        return session.get(url, **kwargs)


_session_manager = SessionManager()


def get_session() -> SessionManager:
    """Return the process-wide manager (not a shared requests session)."""
    return _session_manager
