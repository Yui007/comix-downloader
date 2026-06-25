"""
Compatibility helpers for importing nodriver.

nodriver 0.50.3 ships one generated CDP module as ISO-8859 text without a
Python encoding declaration. Python 3.14 rejects that file before nodriver can
start, so this installs a narrow source-loader fallback for that module only.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import sys
import threading
from pathlib import Path
from types import ModuleType


_TARGET_MODULE = "nodriver.cdp.network"
_HOOK_LOCK = threading.Lock()


class _NodriverNetworkLoader(importlib.machinery.SourceFileLoader):
    """Source loader that re-encodes nodriver.cdp.network if needed."""

    def get_data(self, path: str) -> bytes:
        data = super().get_data(path)

        if self.name != _TARGET_MODULE or Path(path).name != "network.py":
            return data

        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1").encode("utf-8")

        return data


class _NodriverNetworkFinder(importlib.abc.MetaPathFinder):
    """Finder that wraps only nodriver.cdp.network with the fallback loader."""

    def find_spec(self, fullname: str, path=None, target=None):
        if fullname != _TARGET_MODULE:
            return None

        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        if spec and isinstance(spec.loader, importlib.machinery.SourceFileLoader):
            spec.loader = _NodriverNetworkLoader(spec.loader.name, spec.loader.path)
        return spec


def install_nodriver_compat() -> None:
    """Install the nodriver source encoding fallback once."""
    with _HOOK_LOCK:
        if any(isinstance(finder, _NodriverNetworkFinder) for finder in sys.meta_path):
            return
        sys.meta_path.insert(0, _NodriverNetworkFinder())


def load_nodriver() -> ModuleType:
    """Import nodriver after installing the narrow encoding fallback."""
    install_nodriver_compat()
    return importlib.import_module("nodriver")


def load_cdp_page() -> ModuleType:
    """Import nodriver.cdp.page after installing the same fallback."""
    install_nodriver_compat()
    return importlib.import_module("nodriver.cdp.page")
