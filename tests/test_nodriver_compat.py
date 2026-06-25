import contextlib
import importlib
import sys
import tempfile
import unittest
from pathlib import Path

from src.utils import nodriver_compat


@contextlib.contextmanager
def isolated_nodriver_package(package_root: Path):
    saved_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == "nodriver" or name.startswith("nodriver.")
    }
    saved_path = list(sys.path)

    try:
        for name in list(sys.modules):
            if name == "nodriver" or name.startswith("nodriver."):
                del sys.modules[name]

        sys.path.insert(0, str(package_root))
        yield
    finally:
        for name in list(sys.modules):
            if name == "nodriver" or name.startswith("nodriver."):
                del sys.modules[name]

        sys.modules.update(saved_modules)
        sys.path[:] = saved_path


@contextlib.contextmanager
def restored_meta_path():
    saved_meta_path = list(sys.meta_path)
    try:
        yield
    finally:
        sys.meta_path[:] = saved_meta_path


def create_fake_nodriver_package(package_root: Path, files: dict[str, bytes]) -> None:
    cdp_root = package_root / "nodriver" / "cdp"
    cdp_root.mkdir(parents=True)
    (package_root / "nodriver" / "__init__.py").write_text("", encoding="utf-8")
    (cdp_root / "__init__.py").write_text("", encoding="utf-8")

    for relative_path, content in files.items():
        target = package_root / "nodriver" / "cdp" / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


class NodriverCompatTests(unittest.TestCase):
    def test_install_nodriver_compat_is_idempotent(self):
        with restored_meta_path():
            sys.meta_path[:] = [
                finder
                for finder in sys.meta_path
                if not isinstance(finder, nodriver_compat._NodriverNetworkFinder)
            ]

            nodriver_compat.install_nodriver_compat()
            nodriver_compat.install_nodriver_compat()

            installed = [
                finder
                for finder in sys.meta_path
                if isinstance(finder, nodriver_compat._NodriverNetworkFinder)
            ]
            self.assertEqual(len(installed), 1)

    def test_latin1_network_module_imports_successfully(self):
        with tempfile.TemporaryDirectory() as tmpdir, restored_meta_path():
            package_root = Path(tmpdir)
            create_fake_nodriver_package(
                package_root,
                {"network.py": b"VALUE = 1\n# JSON (\xb1Inf).\n"},
            )

            with isolated_nodriver_package(package_root):
                nodriver_compat.install_nodriver_compat()
                module = importlib.import_module("nodriver.cdp.network")

            self.assertEqual(module.VALUE, 1)

    def test_utf8_network_source_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "network.py"
            source = "VALUE = 'ok'\n# JSON (+/-Inf).\n".encode("utf-8")
            path.write_bytes(source)

            loader = nodriver_compat._NodriverNetworkLoader(
                "nodriver.cdp.network",
                str(path),
            )

            self.assertEqual(loader.get_data(str(path)), source)

    def test_non_target_modules_are_not_intercepted(self):
        with tempfile.TemporaryDirectory() as tmpdir, restored_meta_path():
            package_root = Path(tmpdir)
            create_fake_nodriver_package(
                package_root,
                {"other.py": b"VALUE = 1\n# JSON (\xb1Inf).\n"},
            )

            with isolated_nodriver_package(package_root):
                nodriver_compat.install_nodriver_compat()
                with self.assertRaises(SyntaxError):
                    importlib.import_module("nodriver.cdp.other")


if __name__ == "__main__":
    unittest.main()
