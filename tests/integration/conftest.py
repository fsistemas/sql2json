"""Fixtures for real-database integration tests (PostgreSQL and MySQL).

By default these spin up ephemeral database containers **in code** with
[testcontainers](https://testcontainers-python.readthedocs.io/), so a bare

    uv run --extra integration pytest -m integration

just works with no pre-provisioned stack. Each container is started once per
session, seeded with the demo `sales` table (docker/initdb.sql), and torn down
at the end. They are marked `integration` and deselected by default (see
`addopts` in pyproject.toml), so the fast unit suite stays Docker-free.

Override a connection URL with SQL2JSON_TEST_PG_URL / SQL2JSON_TEST_MYSQL_URL to
point at an already-running, already-seeded database instead of starting a
container — this is what `scripts/test-integration.sh` does to reuse the
docker-compose stack. Tests skip cleanly (never fail) when neither an override
nor a container runtime / driver is available, so a machine without either does
not break the build.
"""

import json
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.sql import text

# Ryuk (the testcontainers resource reaper) is flaky under rootless Podman, and
# every container we start is explicitly stopped in a fixture finalizer, so the
# reaper is redundant here. Disable it by default for a clean out-of-the-box run
# on Podman; override by exporting TESTCONTAINERS_RYUK_DISABLED=false.
os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DOCKER_CONFIG_PATH = os.path.join(PROJECT_DIR, "docker", "config.json")
INITDB_PATH = os.path.join(PROJECT_DIR, "docker", "initdb.sql")

# Connection name -> (env var that overrides the URL, testcontainers image).
DATABASES = {
    "pg": ("SQL2JSON_TEST_PG_URL", "postgres:16-alpine"),
    "mysql": ("SQL2JSON_TEST_MYSQL_URL", "mysql:8.0"),
}


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
            "Unset the override env var to start a container instead, or run "
            "./scripts/test-integration.sh."
        )


def _seed(url):
    """Create and populate the demo `sales` table the named queries expect.

    Runs the same docker/initdb.sql the docker-compose services mount, split into
    individual statements (a single DBAPI execute runs one statement). Idempotent
    via `CREATE TABLE IF NOT EXISTS`, but only ever called against a fresh
    container so the seed rows are inserted exactly once.
    """
    with open(INITDB_PATH) as f:
        statements = [s.strip() for s in f.read().split(";") if s.strip()]
    engine = create_engine(url)
    with engine.begin() as con:
        for statement in statements:
            con.execute(text(statement))


def _make_container(name):
    """Construct (don't start) the testcontainers DB container for `name`.

    Skips cleanly when testcontainers is not installed (the `integration` extra).
    """
    _, image = DATABASES[name]
    try:
        if name == "pg":
            from testcontainers.postgres import PostgresContainer

            return PostgresContainer(image)
        from testcontainers.mysql import MySqlContainer

        # Force the pymysql dialect; the default connection URL targets MySQLdb,
        # which we don't ship (the integration extra installs pymysql).
        return MySqlContainer(image, dialect="pymysql")
    except ImportError:
        pytest.skip(
            "testcontainers not installed; install the integration extra "
            "(uv sync --extra integration) or set the override env var."
        )


def _provision(name):
    """Yield a ready, seeded connection URL for `name`.

    Prefers the SQL2JSON_TEST_*_URL override (an already-seeded external DB);
    otherwise starts an ephemeral container, seeds it, and tears it down after
    the session. Skips cleanly when no container runtime is available.
    """
    env_var, _ = DATABASES[name]
    override = os.environ.get(env_var)
    if override:
        _require_reachable(override)
        yield override
        return

    container = _make_container(name)
    try:
        container.start()
    except Exception as exc:  # no Docker/Podman socket, image pull failure, ...
        pytest.skip(
            f"could not start a {name!r} container: {type(exc).__name__}: {exc}. "
            "Start a container runtime (Podman/Docker) or set the override env var."
        )
    try:
        url = container.get_connection_url()
        _seed(url)
        yield url
    finally:
        container.stop()


@pytest.fixture(scope="session")
def pg_url():
    yield from _provision("pg")


@pytest.fixture(scope="session")
def mysql_url():
    yield from _provision("mysql")


@pytest.fixture(params=list(DATABASES))
def database(request, tmp_path):
    """Yield a reachable demo database, exercising named connection lookup.

    Builds a temp config.json that maps the connection name to the provisioned
    URL and reuses the demo queries from docker/config.json, so tests go through
    the same named-connection / named-query resolution as a real CLI invocation.
    """
    name = request.param
    url = request.getfixturevalue(f"{name}_url")

    config = {
        "connections": {name: url},
        "queries": _load_docker_queries(),
    }
    config_path = tmp_path / "integration-config.json"
    config_path.write_text(json.dumps(config))

    return {"name": name, "url": url, "config": str(config_path)}
