"""Thread-local curl_cffi sessions for browser-free image transfer."""

import threading
import time
from typing import Any

from curl_cffi import requests

from .logger import get_logger


logger = get_logger(__name__)


class SessionManager:
    """Provide Chrome-fingerprinted sessions without browser automation."""

    def __init__(self) -> None:
        self._local = threading.local()

    def _session(self):
        session = getattr(self._local, "session", None)
        if session is None:
            session = requests.Session(impersonate="chrome")
            session.headers.update({"Referer": "https://comix.to/"})
            self._local.session = session
        return session

    def get(self, url: str, **kwargs: Any):
        """Perform a GET, retrying a rate-limited response once."""
        kwargs.pop("force_flare", None)
        try:
            response = self._session().get(url, **kwargs)
            if response.status_code == 429:
                logger.warning("Rate limited for %s; retrying after five seconds", url)
                time.sleep(5)
                response = self._session().get(url, **kwargs)
            return response
        except requests.exceptions.RequestException:
            logger.exception("Request failed for %s", url)
            raise


_session_manager: SessionManager | None = None
_session_lock = threading.Lock()


def get_session() -> SessionManager:
    """Return the process-wide manager; each worker receives its own session."""
    global _session_manager
    if _session_manager is None:
        with _session_lock:
            if _session_manager is None:
                _session_manager = SessionManager()
    return _session_manager
