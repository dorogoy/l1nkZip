"""Package version.

Uses importlib.metadata when installed; falls back to reading pyproject.toml
for local development runs that are not installed as a package.
"""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _read_version() -> str:
    try:
        return version("l1nkzip")
    except PackageNotFoundError:
        pass

    import tomllib

    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with pyproject.open("rb") as f:
        return tomllib.load(f)["project"]["version"]


VERSION_NUMBER = _read_version()
