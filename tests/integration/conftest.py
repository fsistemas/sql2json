"""Fixtures for real-database integration tests (PostgreSQL and MySQL).

These tests run against the services defined in `docker-compose.yml`. They are
marked `integration` and deselected by default (see `addopts` in pyproject.toml),
so the fast unit suite stays Docker-free. Run them with:

    ./scripts/test-integration.sh                       # provisions + tears down
    uv run --extra integration pytest -m integration    # against running services

Each test skips cleanly (it never fails) when the target database is unreachable
or its driver is missing, so a machine without Docker does not break the build.
Override the connection URLs with SQL2JSON_TEST_PG_URL / SQL2JSON_TEST_MYSQL_URL.
"""

import json
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.sql import text

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DOCKER_CONFIG_PATH = os.path.join(PROJECT_DIR, "docker", "config.json")

# (connection name, env var overriding the URL, default host-side localhost URL).
# The docker-compose ports bind to 127.0.0.1, so host-run tests use localhost
# rather than the in-network hostnames (postgres / mysql) in docker/config.json.
DATABASES = [
    (
        "pg",
        "SQL2JSON_TEST_PG_URL",
        "postgresql+psycopg2://demo:demo@127.0.0.1:5432/demo",
    ),
    (
        "mysql",
        "SQL2JSON_TEST_MYSQL_URL",
        "mysql+pymysql://demo:demo@127.0.0.1:3306/demo",
    ),
]


def _load_docker_queries():
    """The named queries the README documents (version / sales / sales_by_month)."""
    with open(DOCKER_CONFIG_PATH) as f:
        return json.load(f)["queries"]


def _require_reachable(url):
    """Skip (not fail) when the driver is missing or the database is down."""
    try:
        engine = create_engine(url)
        with engine.connect() as con:
            con.execute(text("SELECT 1"))
    except Exception as exc:  # ModuleNotFoundError, OperationalError, ...
        pytest.skip(
            f"database not reachable at {url!r}: {type(exc).__name__}: {exc}. "
            "Start services with ./scripts/test-integration.sh or "
            "`docker compose up -d postgres mysql`."
        )


@pytest.fixture(params=[name for name, _, _ in DATABASES])
def database(request, tmp_path):
    """Yield a reachable demo database, exercising named connection lookup.

    Builds a temp config.json that maps the connection name to a localhost URL
    and reuses the demo queries from docker/config.json, so tests go through the
    same named-connection / named-query resolution as a real CLI invocation.
    """
    name = request.param
    _, env_var, default_url = next(d for d in DATABASES if d[0] == name)
    url = os.environ.get(env_var, default_url)

    _require_reachable(url)

    config = {
        "connections": {name: url},
        "queries": _load_docker_queries(),
    }
    config_path = tmp_path / "integration-config.json"
    config_path.write_text(json.dumps(config))

    return {"name": name, "url": url, "config": str(config_path)}
