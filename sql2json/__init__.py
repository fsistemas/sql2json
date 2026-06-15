import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .parameter import parse_parameter
from .sql2json import list_connections, list_queries, run_query2json, run_query_by_name


def _package_version() -> str:
    try:
        return version("sql2json")
    except PackageNotFoundError:
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        match = re.search(r'^version = "([^"]+)"', pyproject.read_text(), re.MULTILINE)
        if match:
            return match.group(1)
        raise


__version__ = _package_version()

__all__ = [
    "__version__",
    "parse_parameter",
    "list_connections",
    "list_queries",
    "run_query_by_name",
    "run_query2json",
]
