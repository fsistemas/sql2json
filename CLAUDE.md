# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run all tests (fast, in-memory SQLite — no Docker)
uv run pytest

# Run a single test
uv run pytest tests/test_parameter.py::test_parse_parameter

# Run the real-database integration suite (PostgreSQL + MySQL via docker compose)
# Provisions services, runs the `integration`-marked tests, then tears down.
./scripts/test-integration.sh

# Lint
uv run flake8

# Format
uv run black .

# Type check
uv run --extra dev mypy

# Tests with coverage (gated at 90% via fail_under in pyproject.toml)
uv run --extra dev pytest --cov

# Run the CLI tool (since 0.2.1; `python -m sql2json ...` is equivalent)
sql2json --name default --query default

# Run the official Docker Hub image (multi-arch linux/amd64 + linux/arm64)
podman run --rm docker.io/fsistemas/sql2json --query "SELECT 1 AS a, 2 AS b"
# Docker equivalent:
docker run --rm docker.io/fsistemas/sql2json --query "SELECT 1 AS a, 2 AS b"
# Docker Hub: https://hub.docker.com/r/fsistemas/sql2json

# Build the Docker image (installs sql2json from PyPI; pass VERSION to pin a
# release, omit it for the latest). `podman build ...` works identically.
docker build -t sql2json .                      # latest PyPI release
docker build --build-arg VERSION=0.3.0 -t sql2json .
# The official image is published at docker.io/fsistemas/sql2json (see RELEASING.md).
```

## Architecture

`sql2json` is a CLI tool that runs SQL queries via SQLAlchemy and outputs JSON, CSV, or Excel. Since 0.2.1 it is invoked as the `sql2json` console command (declared in `[project.scripts]`, target `sql2json.__main__:main`); the equivalent `python -m sql2json` form still works. Both dispatch through `fire`.

### One command: autocommit by default, `--read-only` for safe mode

There is a single command (no subcommands). It runs any SQL and **commits by default** (autocommit). It branches on `result.returns_rows`: row-returning statements (SELECT, `... RETURNING`) return rows through the transform pipeline; non-row statements (INSERT/UPDATE/DELETE/DDL) persist and return `{"rowcount": N}`. The rowcount is clamped to `0` (`max(rowcount, 0)`) so a DDL / "count unknown" statement — which drivers report as `-1` on SQLite/PostgreSQL but `0` on MySQL — yields a consistent `{"rowcount": 0}` across databases; real DML counts are `>= 1` and pass through.

`--read-only` (default false) is an opt-in safe mode: the statement still runs but nothing is persisted. Enforcement is hybrid — a real DB read-only transaction is requested where supported (SQLite `PRAGMA query_only = ON`; PostgreSQL/MySQL `SET TRANSACTION READ ONLY`) so a write is rejected up front (reported as `{"rowcount": 0}`, not an error), with an unconditional `con.rollback()` as the portable backstop. A write under `--read-only` prints a notice to stderr and is not persisted; SELECT returns rows normally. `--read-only`/`--read_only` accepts a bare flag or truthy strings (`true/t/yes/y/1/on`) via `_coerce_bool`.

`main()` parses bare flags through `fire`; the only special-cased token is `--version`/`-v`, which prints the version and exits before any query runs.

### Data flow

```
CLI args (fire) → handle_run_query2json() [__main__.py]
  → run_query2json(..., read_only=<bool>) [sql2json.py]   # apply transforms; warn on a read-only write
    → run_query_by_name(..., read_only=<bool>)            # resolves config, loads query by name or from .sql file
      → run_query(..., read_only=<bool>)                  # executes via SQLAlchemy; commits (or rolls back when read_only); returns rows or {"rowcount": N}
        → parse_parameter() per kwarg                      # translates date variable strings to real dates
```

Extra `**kwargs` passed on the CLI (e.g. `--date_from CURRENT_DATE-1`) flow through as both SQL bind parameters (`:date_from` in the query) and are resolved by `parse_parameter` before execution.

### Date variable system (`parameter/parameter_parser.py`)

CLI parameter values that match built-in variables are resolved before being passed to the database:

- `CURRENT_DATE`, `START_CURRENT_MONTH`, `END_CURRENT_MONTH`, `START_CURRENT_YEAR`, `END_CURRENT_YEAR`
- Arithmetic: `CURRENT_DATE-10`, `START_CURRENT_MONTH+1` (days for DATE, months for MONTH vars, years for YEAR vars)
- Custom format via `|` separator: `CURRENT_DATE|%Y-%m-%d 00:00:00`

"Today" is resolved in the local system timezone by default. Pass `--timezone <IANA name>` (e.g. `--timezone UTC`, `--timezone America/New_York`) to pin resolution to a specific timezone. This matters when the tool runs in a different timezone than the intended date boundary.

### Config file

Default path: `~/.sql2json/config.json`. If missing, falls back to an in-memory SQLite DB with `SELECT 1 AS a, 2 AS b` (this is how tests run — no external DB needed).

**Note:** The config accepts both `"connections"` (correct spelling) and `"conections"` (legacy typo). `"connections"` takes priority when both keys are present. Existing configs with `"conections"` continue to work.

Query values prefixed with `@` are treated as file paths to `.sql` files.

### Output transformations (`run_query2json`)

| Flag | Effect |
|---|---|
| `--first` | Return only the first row |
| `--key` | Extract a single column as the value (or use as dict key with `--value`) |
| `--value` | Used with `--key` to produce `{key_col: value_col}` dicts |
| `--wrapper` | Wrap the result. `True`/bare flag wraps under `{"data": [...]}`; a non-empty string wraps under that key (`--wrapper items` → `{"items": [...]}`); `False`/`""` returns it unwrapped |
| `--jsonkeys` | Comma-separated column names whose string values should be parsed as JSON |
| `--read-only` | Opt-in safe mode: the statement runs but nothing persists (DB read-only on SQLite/PostgreSQL/MySQL, rollback backstop elsewhere). A write prints a stderr notice and returns `{"rowcount": ...}` without persisting; SELECT returns rows normally |
| `--format` | `json` (default), `csv`, or `excel` |
| `--output` | Save to file instead of printing; filename supports `{CURRENT_DATE}` etc. |
| `--timezone` | IANA timezone name for resolving date variables (e.g. `UTC`, `America/New_York`). Defaults to local system timezone. |

### Tests

- **Unit tests** (`uv run pytest`) use the in-memory SQLite fallback — fast, no Docker, no external DB.
- **Integration tests** (`tests/integration/`, marked `integration`, deselected by default via `addopts` in `pyproject.toml`) run against real PostgreSQL and MySQL. By default they provision ephemeral databases **in code** with [testcontainers](https://testcontainers-python.readthedocs.io/) — given a running Docker/Podman, `uv run --extra integration pytest -m integration` just works, no pre-provisioned stack required. The session-scoped `pg_url`/`mysql_url` fixtures start `postgres:16-alpine` / `mysql:8.0`, seed the demo `sales` table from `docker/initdb.sql`, and tear the containers down. `DOCKER_HOST` must point at the container socket (e.g. `unix:///run/user/1000/podman/podman.sock` for rootless Podman), and `TESTCONTAINERS_RYUK_DISABLED=true` is set automatically (the Ryuk reaper is flaky under rootless Podman; containers are stopped explicitly). Set `SQL2JSON_TEST_PG_URL` / `SQL2JSON_TEST_MYSQL_URL` to point at an already-running, already-seeded external database instead of starting containers; `./scripts/test-integration.sh` uses exactly this to drive and reuse the `docker-compose.yml` stack. The `database` fixture builds a temp config that maps a connection name to the provisioned URL and reuses the named queries from `docker/config.json`. Tests `pytest.skip` cleanly when no container runtime is available, a database is unreachable, or a driver (`psycopg2-binary` / `pymysql` / `testcontainers`, the `integration` extra) is missing.

## Release process

### Checklist

1. **Bump version** in `pyproject.toml`:
   ```toml
   version = "0.1.12"
   ```

2. **Update `CHANGELOG.md`** — add a new `[0.1.12]` section at the top following Keep a Changelog format.

3. **Run tests and lint**:
   ```bash
   uv run pytest
   uv run flake8
   ```

4. **Commit**:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to 0.1.12"
   ```

5. **Tag** (always prefix with `v`):
   ```bash
   git tag v0.1.12
   ```

6. **Push commit and tag together**:
   ```bash
   git push origin master --tags
   ```

7. **Build and publish to PyPI**:
   ```bash
   uv build
   uv publish
   ```
   `uv build` produces `dist/sql2json-0.1.12.tar.gz` and the wheel. `uv publish` uploads to PyPI (requires a token configured via `UV_PUBLISH_TOKEN` or `~/.pypirc`).

8. **Publish the Docker image** to `docker.io/fsistemas/sql2json` from your local machine (not CI). The image installs `sql2json==<version>` from PyPI, so this runs **after** step 7. The maintainer uses Podman; for multi-arch on an amd64 machine, the tested local path is rootful Podman (`sudo podman`) with host-level `qemu-user-static`/`binfmt_misc`, because rootless Podman can fail to execute arm64 builds. `docker buildx` is equivalent for contributors using real Docker BuildKit. Push the immutable `:X.Y.Z` tag every release and move `:latest` only for stable releases. See `RELEASING.md` for the full Podman/Docker commands and the verify step.

### Notes

- Build artifacts (`dist/`, `*.egg-info/`) are in `.gitignore` — never commit them.
- The build backend is **hatchling** (set in `pyproject.toml`). Do not use `python setup.py` or `setuptools` commands.
