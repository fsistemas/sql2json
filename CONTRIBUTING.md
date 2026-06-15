# Contributing to sql2json

Thanks for contributing! This project runs a set of automated quality gates on
every pull request and on pushes to `master` (see
[`.github/workflows/ci.yml`](.github/workflows/ci.yml)). Running them locally
before you push keeps the feedback loop fast.

## Setup

```bash
uv sync --extra dev
```

This installs the runtime dependencies plus the `dev` tooling (black, flake8,
mypy, pytest, pytest-cov, pre-commit, type stubs).

## Quality gates

All four checks must pass. They mirror exactly what CI runs.

| Check | Command | Notes |
|---|---|---|
| Format | `uv run --extra dev black --check .` | Use `black .` (no `--check`) to fix in place. Target version is pinned to `py310` in `pyproject.toml`. |
| Lint | `uv run --extra dev flake8` | Config in `.flake8` (max line length 88). |
| Types | `uv run --extra dev mypy` | Checks the `sql2json` package. `fire` has no stubs, so it carries a narrow, documented `ignore_missing_imports` override in `pyproject.toml`. |
| Tests + coverage | `uv run --extra dev pytest --cov` | Fast in-memory SQLite suite, no Docker. Coverage is gated at **90%** (`fail_under` in `pyproject.toml`). |

Run a single test:

```bash
uv run --extra dev pytest tests/test_parameter.py::test_parse_parameter
```

### Integration tests (optional)

The real-database suite (PostgreSQL + MySQL via Docker) is deselected by default.
Provision the services, run it, and tear down with:

```bash
./scripts/test-integration.sh
```

See the [README](README.md#real-database-verification) for details.

## Supported Python versions

`sql2json` targets **Python 3.10–3.13** (`requires-python >=3.10`). CI runs the
unit suite against all four versions; black, flake8, and mypy run once on a
single version. Avoid syntax or APIs unavailable on 3.10.

## Pull requests

- Keep PRs focused; follow [Conventional Commits](https://www.conventionalcommits.org/)
  for commit messages (e.g. `fix:`, `feat:`, `ci:`, `docs:`).
- Update `CHANGELOG.md` under `[Unreleased]` when behavior changes.
- Make sure all quality gates above pass locally before pushing.
