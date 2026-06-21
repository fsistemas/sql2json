# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Official Docker image published to [`docker.io/fsistemas/sql2json`](https://hub.docker.com/r/fsistemas/sql2json), so the tool can be run with `podman run docker.io/fsistemas/sql2json ...` (or `docker run ...`) without building from source. It is now published as a multi-arch image for `linux/amd64` and `linux/arm64`. Supported tags: `latest` (newest stable) and immutable `X.Y.Z` (pinned). Documented in the README "Docker" section.

### Changed
- The `Dockerfile` now installs `sql2json` from PyPI (build arg `VERSION` pins a release; omitted installs the latest) instead of copying the working tree, so a tagged image always matches the published release. Its entrypoint is now the `sql2json` console script (was `python -m sql2json`), and it carries OCI image labels.
- Documented the local (Podman / Docker) image publish + verify step in `RELEASING.md` and CLAUDE.md, run after the PyPI publish. The tested multi-arch local path is rootful Podman (`sudo podman`) with host-level QEMU/binfmt on an amd64 maintainer machine.
- Reworked install/upgrade instructions across `README.md`, `AGENTS.md`, and `skills/sql2json/SKILL.md` to be cross-platform and environment-aware (Linux, macOS, Windows). The recommended install is now an isolated tool (`uv tool install` / `pipx install`) that bundles the Postgres and MySQL drivers by default (`"sql2json[postgres,mysql]"`), works on PEP 668 externally-managed systems, and documents the extras-quoting gotcha, the SQLite-only minimal variant, adding drivers later, the `--break-system-packages` escape hatch, and how to upgrade while keeping the drivers.

## [0.2.1] - 2026-06-19

### Added
- `sql2json` console entry point (`[project.scripts]` → `sql2json.__main__:main`), so the tool can be run as a plain `sql2json ...` command after install instead of only `python -m sql2json ...`. The `python -m sql2json` form continues to work unchanged. This also enables isolated global installs via `pipx install sql2json` / `uv tool install sql2json`.

## [0.2.0] - 2026-06-15

> **`0.2.0` is a minor bump that ships breaking changes under the pre-1.0 SemVer
> convention.** The public Python API is tightened: the `sql2json.parameter`
> date helpers (`is_number`, `first_day_month`, `first_day_year`,
> `last_day_month`, `last_day_year`, `parse_field`, `parse_formula`) are now
> private and no longer re-exported. `parse_parameter` remains the supported
> public entry point. `sql2json` is pre-1.0, so this ships as a minor bump with
> **no formal deprecation cycle**.
>
> This release includes API-boundary work: privatizing helpers, adding
> explicit `__all__` exports, and single-sourcing the package version via
> `importlib.metadata.version("sql2json")`.
>
> **Migration:** if you imported any of those date helpers from
> `sql2json.parameter`, switch to the public `parse_parameter` for
> date-variable resolution.

### Added
- CI quality gates in `.github/workflows/ci.yml`: a `quality` job running `black --check`, `flake8`, and `mypy`; a `unit` job running the test suite with coverage across Python 3.10–3.13; and the existing database `integration` job. Coverage is gated at 90% via `fail_under` in `pyproject.toml`. CI runs on pull requests and pushes to `master`.
- `CONTRIBUTING.md` documenting the local quality-gate commands and supported Python matrix; the README gains a "Quality gates" section.
- `[tool.black]`, `[tool.mypy]`, and `[tool.coverage]` configuration in `pyproject.toml`. `black` target is pinned to `py310`; `mypy` carries a narrow, documented `ignore_missing_imports` override for the stub-less `fire` import.
- Real-database integration test suite (`tests/integration/`) covering the PostgreSQL and MySQL demo paths: named connection lookup, named query lookup, bind parameters, Decimal values, and JSON serialization. Tests are marked `integration` and deselected by default, so `uv run pytest` stays fast and Docker-free. Run them with `./scripts/test-integration.sh` (provisions the `docker-compose.yml` services, runs the suite, tears down) or `uv run --extra integration pytest -m integration tests/integration` against already-running services. Each test skips cleanly when its database is unreachable. A `.github/workflows/ci.yml` `integration` job provisions the services in CI.
- Explicit `__all__` exports for the supported top-level Python API and `sql2json.parameter` surface.
- Python API documentation and runnable examples under `examples/python_api`.
- Project hygiene for public GitHub/PyPI: `LICENSE` (MIT), `SECURITY.md` (security model and private vulnerability reporting), and `RELEASING.md` (maintainer-only release process).
- Packaging metadata in `pyproject.toml`: `readme`, `license`/`license-files`, keywords, trove classifiers, and `[project.urls]` (Homepage, Repository, Issues, Changelog) so PyPI links to source, issues, docs, and license.
- User-facing database driver extras: `pip install "sql2json[postgres]"` (psycopg2-binary) and `sql2json[mysql]` (PyMySQL).
- `--timezone` flag: accepts an IANA timezone name (e.g. `--timezone America/New_York`, `--timezone UTC`) and uses it when resolving `CURRENT_DATE`, `START_CURRENT_MONTH`, and all other date variables. Defaults to local system timezone (backward-compatible). An invalid timezone name produces a structured JSON error on stderr and a non-zero exit code.

### Changed
- Package version is now single-sourced from installed package metadata via `importlib.metadata.version("sql2json")`.
- `sql2json.parameter` now only exports the public `parse_parameter` entry point; lower-level date helper functions are private implementation details.
- `run_query2json` now carries an explicit `-> Union[str, dict, list]` return annotation so the package type-checks cleanly under mypy.

## [0.1.11] - 2026-05-16

### Added
- `--list-connections`: prints a JSON array of configured connection names and exits
- `--list-queries`: prints a JSON array of configured query names and exits
- `list_connections(config_path)` and `list_queries(config_path)` exported from the Python package
- Config file lookup now checks `./sql2json.json` and `./.sql2json/config.json` in the current directory before falling back to `~/.sql2json/config.json`
- Structured JSON error output on stderr (`{"error": "...", "type": "..."}`) when the CLI fails; stdout remains empty on error and exit code is non-zero

### Fixed
- SQLAlchemy 2.x compatibility: `row.keys()` replaced with `result_proxy.keys()` in row mapping
- `--config` kwarg is now popped before being forwarded to SQLAlchemy; previously it was incorrectly passed as a SQL bind parameter
- Build backend corrected from the non-existent `uv.build` to `hatchling`

### Changed
- AGENTS.md rewritten: removed references to non-existent `--description` and `--format dict` flags; added discovery, error handling, and Python API sections

## [0.1.10] - 2020-05-25

### Added
- Add support to write output to csv, excel or json file using --output sales.csv, --output sales.csv, --output sales.json
- New parameter output, the name of the file to write the data. With custom variables like --output Sales-{CURRENT_DATE-5}_{CURRENT_DATE+2}
- New parameter format(default=json). Values json, csv, excel
- Add examples to README.md for output, format

## [0.1.9] - 2020-01-19

### Added
- Support map column value as key, value ussing --key column1 --value column2
- Add README.md, improve documentation

### Removed
- README.rst

## [0.1.8] - 2020-01-18

### Added
- Support map column value as key, value ussing --key column1 --value column2
- New flag jsonkeys: coma separated columns to convert JSON functions result as JSON not as string

## [0.1.7] - 2020-01-04

### Added
- Support to read sql from external file using --query @FULL_PATH_TO_MY_FILE
- You can pass a custom config file as parameter --config. Ex. --config /Users/myuser/my-config.json

### Changed
- FIX to accept any parameter, not only date formulas
- Remove empty flag: true/false from response when user pass wrapper flag
