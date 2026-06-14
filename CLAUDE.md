# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/test_parameter.py::test_parse_parameter

# Lint
uv run flake8

# Format
uv run black .

# Run the CLI tool
python -m sql2json --name default --query default

# Build Docker image
docker build -t sql2json .
```

## Architecture

`sql2json` is a CLI tool that runs SQL queries via SQLAlchemy and outputs JSON, CSV, or Excel. It is invoked as `python -m sql2json` (entry point: `__main__.py` using `fire`).

### Data flow

```
CLI args (fire) → handle_run_query2json() [__main__.py]
  → run_query2json() [sql2json.py]       # applies result transformations (first/key/value/wrapper/jsonkeys)
    → run_query_by_name()                # resolves config, loads query by name or from .sql file
      → run_query()                      # executes via SQLAlchemy, kwargs become SQL :params
        → parse_parameter() per kwarg   # translates date variable strings to real dates
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
| `--wrapper` | Wrap the result list in `{"data": [...]}` |
| `--jsonkeys` | Comma-separated column names whose string values should be parsed as JSON |
| `--format` | `json` (default), `csv`, or `excel` |
| `--output` | Save to file instead of printing; filename supports `{CURRENT_DATE}` etc. |
| `--timezone` | IANA timezone name for resolving date variables (e.g. `UTC`, `America/New_York`). Defaults to local system timezone. |

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

### Notes

- Build artifacts (`dist/`, `*.egg-info/`) are in `.gitignore` — never commit them.
- The build backend is **hatchling** (set in `pyproject.toml`). Do not use `python setup.py` or `setuptools` commands.
