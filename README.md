# sql2json

Run SQL queries and get JSON (or CSV) on stdout — pipe it anywhere.

`sql2json` connects to any SQLAlchemy-supported database, executes a query, and writes the results as JSON to standard output. No server, no framework, no boilerplate.

```bash
sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1"
# → [{"month": "January", "sales": 5000}, {"month": "February", "sales": 3000}]
```

## Use cases

- **Scheduled reports**: run a cron job that pulls yesterday's sales and posts the JSON to a dashboard (Geckoboard, Grafana, etc.)
- **Shell pipelines**: pipe query results into `jq`, `curl`, or any CLI tool that speaks JSON
- **AI agent data retrieval**: let an LLM agent query your database with a single subprocess call — see [AGENTS.md](AGENTS.md)
- **ETL glue**: extract rows as JSON, transform with standard tools, load elsewhere
- **Monitoring & alerting**: script threshold checks against live database metrics

## Install

```bash
pip install sql2json
```

SQLite works out of the box (it ships with Python). For PostgreSQL or MySQL,
install the matching driver extra:

```bash
pip install "sql2json[postgres]"   # psycopg2-binary
pip install "sql2json[mysql]"      # PyMySQL
pip install "sql2json[postgres,mysql]"
```

Other databases work too — install any
[SQLAlchemy-supported driver](https://docs.sqlalchemy.org/en/20/dialects/) (e.g.
`pyodbc` for MS SQL Server) alongside `sql2json`.

### Running it

Once installed, invoke the tool directly:

```bash
sql2json --name default --query default
```

The `sql2json` command is available **since v0.2.1**. The original
`python -m sql2json ...` form still works and is equivalent — use it on `0.2.0`
and earlier, or whenever the package is installed but its scripts directory is
not on your `PATH`.

For a global, isolated install that puts `sql2json` on your `PATH` without
touching your project environments:

```bash
pipx install sql2json
# or
uv tool install sql2json
```

## Docker

An official image is published to Docker Hub at
[`docker.io/fsistemas/sql2json`](https://hub.docker.com/r/fsistemas/sql2json).
It bundles drivers for PostgreSQL (`psycopg2-binary`) and MySQL / MariaDB
(`PyMySQL`) in addition to SQLite, which is built into Python, and is built for
both `linux/amd64` and `linux/arm64`.

The examples below use [Podman](https://podman.io/); every command works
identically with `docker` — just swap the executable name.

Quick test without a config file (pulls the image on first run):

```bash
podman run --rm docker.io/fsistemas/sql2json --query "SELECT 1 AS a, 2 AS b"
# → [{"a": 1, "b": 2}]
```

### Supported tags

| Tag | Meaning |
|---|---|
| `latest` | Newest **stable** release. Moves on every release — convenient, but not pinned. |
| `X.Y.Z` (e.g. `0.2.1`) | A specific release. **Immutable** — recommended for production and CI. |

```bash
podman pull docker.io/fsistemas/sql2json:0.2.1   # pin a release
podman pull docker.io/fsistemas/sql2json:latest  # newest stable
```

### Usage

The image runs as an unprivileged user (`app`), whose home is `/home/app`, so
config is read from `/home/app/.sql2json`.

Run with your own config by mounting `~/.sql2json`:

```bash
podman run --rm \
  -v ~/.sql2json:/home/app/.sql2json \
  docker.io/fsistemas/sql2json --name default --query sales_monthly --date_from "START_CURRENT_MONTH-1"
```

For SQLite, mount both the config directory and the database file. Point the connection string in your config to the in-container path:

```bash
podman run --rm \
  -v ~/.sql2json:/home/app/.sql2json \
  -v /path/to/mydb.sqlite:/data/mydb.sqlite \
  docker.io/fsistemas/sql2json --name default --query default
```

```json
{
    "connections": {
        "default": "sqlite:////data/mydb.sqlite"
    }
}
```

Write output files by mounting a host directory to `/workspace`, the container working directory. Because the container runs as a non-root user, map the container user to your host user so the written files are owned by you — `--userns=keep-id` for Podman, `--user $(id -u):$(id -g)` for Docker:

```bash
podman run --rm --userns=keep-id \
  -v ~/.sql2json:/home/app/.sql2json \
  -v $(pwd)/reports:/workspace \
  docker.io/fsistemas/sql2json --name default --query sales_monthly \
    --format csv --output "Sales_{CURRENT_DATE}"
# → ./reports/Sales_2026-05-17.csv on the host

# Docker equivalent:
docker run --rm --user $(id -u):$(id -g) \
  -v ~/.sql2json:/home/app/.sql2json \
  -v $(pwd)/reports:/workspace \
  docker.io/fsistemas/sql2json --name default --query sales_monthly \
    --format csv --output "Sales_{CURRENT_DATE}"
```

MS SQL Server needs system-level ODBC libraries, so install the driver in a derived image:

```dockerfile
FROM docker.io/fsistemas/sql2json
RUN pip install --no-cache-dir pyodbc
```

### Build from source (development)

The published image installs `sql2json` from PyPI. To build an image from a
local checkout instead — for example to try an unreleased change — pass the
`VERSION` build arg (or omit it to install the latest PyPI release):

```bash
podman build -t sql2json .                       # latest PyPI release
podman build --build-arg VERSION=0.2.1 -t sql2json .   # pin a release
podman run --rm sql2json --query "SELECT 1 AS a, 2 AS b"
```

### Try it with docker compose

The repo includes a `docker-compose.yml` that starts PostgreSQL and MySQL with demo-only credentials, a small `sales` table, and a pre-wired `docker/config.json`. The database ports bind to `127.0.0.1` for local testing.

Start the databases:

```bash
docker compose up -d postgres mysql
```

Run queries against PostgreSQL:

```bash
docker compose run --rm sql2json --name pg --query version
# → [{"version": "PostgreSQL 16.x ..."}]

docker compose run --rm sql2json --name pg --query sales
# → [{"id": 1, "month": "January", "amount": 5000.0}, ...]

docker compose run --rm sql2json --name pg --query sales_by_month --min_amount 4000
# → [{"month": "January", "amount": 5000.0}, {"month": "March", "amount": 7100.75}]
```

Run the same demo queries against MySQL by switching `--name`:

```bash
docker compose run --rm sql2json --name mysql --query sales
```

Tear down when done:

```bash
docker compose down
```

The demo config lives in `docker/config.json` and the seed table in `docker/initdb.sql`.

### Real database verification

The fast unit suite runs against in-memory SQLite and needs no Docker:

```bash
uv run pytest
```

A separate, opt-in integration suite verifies the documented demo paths (named
connection lookup, named query lookup, bind parameters, Decimal values, and JSON
serialization) against the real PostgreSQL and MySQL services. The one command
below provisions the `docker-compose.yml` services, runs the suite, and tears
them down:

```bash
./scripts/test-integration.sh
```

The integration tests are marked `integration` and deselected by default, so
`uv run pytest` stays Docker-free. To run them against already-running services
(or a different host/port via `SQL2JSON_TEST_PG_URL` / `SQL2JSON_TEST_MYSQL_URL`):

```bash
docker compose up -d postgres mysql
uv run --extra integration pytest -m integration tests/integration
```

Each test **skips cleanly** when its database is unreachable, so a machine
without Docker never sees failures. In CI, the `integration` job in
`.github/workflows/ci.yml` provisions the services and runs the same suite.

### Quality gates

The same checks that CI enforces can be run locally. See
[CONTRIBUTING.md](CONTRIBUTING.md) for details.

```bash
uv run --extra dev black --check .   # formatting
uv run --extra dev flake8            # linting
uv run --extra dev mypy              # type checking
uv run --extra dev pytest --cov      # tests + coverage (gated at 90%)
```

`uv run --extra dev black .` reformats in place. CI (`.github/workflows/ci.yml`)
runs these on every pull request and on pushes to `master`: a `quality` job for
black/flake8/mypy, a `unit` job across Python 3.10–3.13 with the coverage gate,
and the database `integration` job.

## Quick start

**1. Create the config file:**

```bash
mkdir -p ~/.sql2json
cat > ~/.sql2json/config.json << 'EOF'
{
    "connections": {
        "default": "sqlite:///mydb.sqlite"
    },
    "queries": {
        "default": "SELECT 1 AS a, 2 AS b"
    }
}
EOF
```

**2. Run a query:**

```bash
sql2json
# → [{"a": 1, "b": 2}]
```

**3. Try inline SQL:**

```bash
sql2json --name default --query "SELECT date('now') AS today"
# → [{"today": "2026-05-16"}]
```

## Configuration

By default `sql2json` looks for a config file in this order:

1. `./sql2json.json` (current directory)
2. `./.sql2json/config.json` (current directory)
3. `~/.sql2json/config.json` (home directory)

Use `--config /path/to/config.json` to override.

### Config file format

```json
{
    "connections": {
        "default": "sqlite:///test.db",
        "postgres": "postgresql://scott:tiger@localhost:5432/mydb",
        "mysql": "mysql://scott:tiger@localhost/foo"
    },
    "queries": {
        "default": "SELECT 1 AS a, 2 AS b",
        "sales_monthly": "SELECT inv.month, SUM(inv.amount) AS sales FROM invoices inv WHERE inv.date >= :date_from",
        "total_sales": "SELECT SUM(inv.amount) AS sales FROM invoices inv WHERE inv.date >= :date_from",
        "long_query": "@/path/to/my_query.sql"
    }
}
```

> **Note:** Both `"connections"` and `"conections"` (legacy typo) are accepted. Existing config files do not need to be updated.

Connection strings follow [SQLAlchemy URL format](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls). Query values starting with `@` are treated as paths to `.sql` files.

## CLI reference

```bash
sql2json [options] [--param value ...]
```

| Flag | Default | Description |
|---|---|---|
| `--name` | `default` | Connection name from config, or a raw SQLAlchemy URL |
| `--query` | `default` | Named query, raw SQL string, or `@/path/file.sql` |
| `--config` | _(lookup order above)_ | Path to a specific config file |
| `--first` | `False` | Return only the first row (object, not array) |
| `--key` | `""` | Extract one column as value (scalar with `--first`), or dict key (with `--value`) |
| `--value` | `""` | Used with `--key` to produce `{key_col: value_col}` dicts |
| `--wrapper` | `False` | Wrap result in `{"data": [...]}` (bare `--wrapper`/`True`); pass a string (e.g. `--wrapper=items`) to wrap under a custom key: `{"items": [...]}` |
| `--jsonkeys` | `""` | Comma-separated columns whose string values should be parsed as JSON |
| `--format` | `json` | Output format: `json`, `csv`, `excel` |
| `--output` | _(stdout)_ | Save to file; filename supports `{CURRENT_DATE}` etc. |
| `--list-connections` | — | Print JSON array of configured connection names and exit |
| `--list-queries` | — | Print JSON array of configured query names and exit |

Extra `--key value` flags become SQL bind parameters (`:key` in your query).

### Discovery

Before writing a query, inspect what is configured:

```bash
sql2json --list-connections
# → ["default", "mysql", "reporting"]

sql2json --list-queries
# → ["default", "sales_monthly", "total_sales"]
```

## Date variables

Extra parameters whose values match a built-in variable are resolved to real dates before the query runs:

| Variable | Resolves to |
|---|---|
| `CURRENT_DATE` | Today's date |
| `START_CURRENT_MONTH` | First day of the current month |
| `END_CURRENT_MONTH` | Last day of the current month |
| `START_CURRENT_YEAR` | First day of the current year |
| `END_CURRENT_YEAR` | Last day of the current year |

**Arithmetic** — the unit depends on the variable:

```
CURRENT_DATE-7          → 7 days ago
START_CURRENT_MONTH+1   → first day of next month
START_CURRENT_YEAR-1    → first day of last year
```

**Custom format** — append `|strftime_format`:

```bash
--min_date "CURRENT_DATE|%Y-%m-%d 00:00:00"
# → "2026-05-16 00:00:00"

--min_date "START_CURRENT_YEAR|%Y-%m-%d 00:00:00"
# → "2026-01-01 00:00:00"
```

## Output transformations

### Array of objects (default)

```bash
sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1"
```
```json
[
    {"month": "January", "sales": 5000},
    {"month": "February", "sales": 3000}
]
```

### First row only (`--first`)

```bash
sql2json --name mysql --query total_sales --date_from "CURRENT_DATE-10" --first
```
```json
{"sales": 500}
```

### Single value (`--first --key`)

```bash
sql2json --name mysql --query total_sales --date_from "CURRENT_DATE-10" --first --key sales
```
```
500
```

### Key-value pairs (`--key --value`)

```bash
sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1" --key month --value sales
```
```json
[
    {"January": 5000},
    {"February": 3000}
]
```

### Wrapped for dashboards (`--wrapper`)

```bash
sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1" --wrapper
```
```json
{
    "data": [
        {"month": "January", "sales": 5000},
        {"month": "February", "sales": 3000}
    ]
}
```

Pass a string to wrap under a custom key instead of `data`:

```bash
sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1" --wrapper=items
```
```json
{
    "items": [
        {"month": "January", "sales": 5000},
        {"month": "February", "sales": 3000}
    ]
}
```

### Parse JSON columns (`--jsonkeys`)

When a column contains a JSON string from a database JSON function, use `--jsonkeys` to parse it:

```bash
sql2json --name mysql --query json_report --jsonkeys "payload,metadata"
```

Without `--jsonkeys` those columns would be escaped strings; with it they are inlined as JSON.

### Inline SQL

No need to define every query in the config file:

```bash
sql2json --name mysql --query "SELECT NOW() AS ts" --first --key ts
```

### External `.sql` file

```bash
# Defined in config.json as "@/path/to/file.sql"
sql2json --name mysql --query long_query --min_age 18

# Or pass the path directly
sql2json --name mysql --query "@/path/to/my_query.sql" --min_age 18
```

## File output

Use `--output` to write to a file instead of stdout. The `--format` flag controls the extension (default `json`):

```bash
# CSV file
sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1" --format csv --output Sales
# → Sales.csv

# Excel file
sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1" --format excel --output Sales
# → Sales.xls

# JSON file
sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1" --format json --output Sales
# → Sales.json
```

**Dated filenames** — use date variables in `--output`:

```bash
sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH" \
    --format csv --output "Sales_{START_CURRENT_MONTH}_{CURRENT_DATE}"
# → Sales_2026-05-01_2026-05-16.csv

sql2json --name mysql --query sales_monthly --date_from "CURRENT_DATE" \
    --format csv --output "reports/Sales_{CURRENT_DATE}"
# → reports/Sales_2026-05-16.csv
```

> **Note:** `--output` does not create directories. Create the target folder first.

> **Note:** CSV requires `--output` (it cannot be written to stdout).

## Python API

The supported Python API mirrors the user-facing CLI capabilities while keeping implementation details private:

```python
from sql2json import list_connections, list_queries, run_query2json, run_query_by_name

rows = run_query2json(
    name="sqlite:///:memory:",
    query="SELECT :person_name AS name, :score AS score",
    person_name="Ada",
    score=42,
)

connections = list_connections("/path/to/config.json")
queries = list_queries("/path/to/config.json")
```

Use `run_query2json()` for inline SQL, named queries, SQL files with `@/path.sql`, bind/date parameters, `first`, `key`, `value`, `wrapper`, `jsonkeys`, and `timezone`. Use `run_query_by_name()` when you specifically want the lower-level named connection/query call.

Python API errors are normal Python exceptions. The CLI-only JSON stderr envelope is not used by the Python API.

Supported public imports are exported from `sql2json.__all__`. Internal helpers in `sql2json.sql2json`, `sql2json.__main__`, or `sql2json.parameter.parameter_parser` are implementation details and should not be imported by users. `sql2json.parameter.parse_parameter` remains public for date-variable resolution; lower-level date helper functions are private.

See [examples/python_api](examples/python_api) for runnable examples covering named queries, inline SQL, discovery, output shapes, JSON columns, date parameters, SQL files, and exception handling.

### Public API surface

`sql2json` treats the following as its supported, public surface. Everything else is an implementation detail that may change without notice.

**Python API** — the names exported from `sql2json.__all__`:

- `run_query2json`, `run_query_by_name`
- `list_connections`, `list_queries`
- `parse_parameter` (from `sql2json.parameter`)
- `__version__`

**CLI compatibility contract** — the supported, stable CLI behavior:

- Documented flags: `--name`, `--query`, plus `--first`, `--key`, `--value`, `--wrapper`, `--jsonkeys`, `--format`, `--output`, `--timezone`, and arbitrary `--<bind_param>` values.
- Output shapes: JSON to stdout (default), CSV and Excel via `--format`/`--output`.
- Error contract: a structured JSON error envelope on stderr with a non-zero exit code.

**Versioning:** `sql2json` is pre-1.0 (`0.x`) and carries **no API stability guarantee** under SemVer — breaking changes ship in a minor bump (e.g. `0.1.x → 0.2.0`), not a major. A real stability contract would be an explicit `1.0.0` decision.

## For AI agents

`sql2json` is designed to be called as a subprocess by AI agents and LLMs. It outputs clean JSON to stdout, structured errors to stderr, and supports discovery commands so an agent can orient itself before querying.

See [AGENTS.md](AGENTS.md) for the full agent integration guide, including discovery flags, error handling, the Python API, and security notes.

## Contributing

Issues and pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for
local setup and the quality gates. Releases are maintainer-only
([RELEASING.md](RELEASING.md)).

## Security

`sql2json` executes the SQL it is given and config files may contain database
credentials. See [SECURITY.md](SECURITY.md) for the security model and how to
report a vulnerability privately.

## License

[MIT](LICENSE) © Francisco Perez
