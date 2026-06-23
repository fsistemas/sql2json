# Using `sql2json` with AI Agents and LLMs

`sql2json` runs SQL queries via SQLAlchemy and outputs JSON or CSV to stdout. It is invoked as a CLI tool or imported as a Python package — no framework coupling, no MCP server required.

> **Invocation:** examples below use the `sql2json` command, available **since v0.2.1**. On `0.2.0` and earlier — or when the package's scripts directory is not on `PATH` — substitute the equivalent `python -m sql2json ...` form (on Windows, `py -m sql2json ...`).

---

## Install & upgrade (for agents)

Install `sql2json` as an isolated tool, **with the database drivers bundled** so
queries against PostgreSQL/MySQL work without a follow-up step:

```bash
uv tool install "sql2json[postgres,mysql]"
# or
pipx install "sql2json[postgres,mysql]"
```

Why these methods matter in a sandbox:

- They work on **externally-managed** environments (Manjaro/Arch, Debian 12+,
  Ubuntu 23.04+, Homebrew Python), where a plain `pip install` is refused with
  `error: externally-managed-environment` ([PEP 668](https://peps.python.org/pep-0668/)).
- They expose `sql2json` on `PATH` (in `~/.local/bin`; run `pipx ensurepath` if
  it is missing) without mutating any project environment.

**Quote the extras.** In bash/zsh the brackets are glob characters, so the spec
must be quoted — `"sql2json[postgres,mysql]"` — or the shell expands it and the
install fails before the installer runs. In PowerShell use single quotes:
`'sql2json[postgres,mysql]'`.

**Selecting drivers:** `[postgres]` (psycopg2) or `[mysql]` (pymysql) for a
single database; bare `sql2json` is **SQLite only** — connecting to
Postgres/MySQL without the extras raises `ModuleNotFoundError: psycopg2` /
`pymysql`. For other databases (e.g. MS SQL Server's `pyodbc`), install the
driver alongside: `uv tool install "sql2json" --with pyodbc`.

If `sql2json` already exists but lacks a driver, reinstall with the extras
(`uv tool install "sql2json[postgres,mysql]" --force`) or inject it
(`pipx inject sql2json psycopg2-binary pymysql`).

**Inside a project/venv** (library use), add it as a dependency instead, keeping
the extras: `uv add "sql2json[postgres,mysql]"` or, in an activated venv,
`pip install "sql2json[postgres,mysql]"`.

**Upgrade** (carry the extras so drivers stay installed):

```bash
uv tool upgrade sql2json                              # or: uv tool install "sql2json[postgres,mysql]" --force
pipx upgrade sql2json
pip install --upgrade "sql2json[postgres,mysql]"      # inside a venv
```

Check the installed version with `uv tool list`, `pipx list`, or
`python -c "import importlib.metadata as m; print(m.version('sql2json'))"`.

---

## Strategy for Agents

Map a natural language request to these parameters:

1. **Identify the connection** (`--name`): which database to use.
2. **Select the query** (`--query`): prefer a named query from `config.json`, using connection-scoped queries when available; otherwise use raw inline SQL or a path to a `.sql` file prefixed with `@`.
3. **Resolve named-query precedence**: for `--name <conn> --query <name>`, sql2json checks `connection_queries.<conn>.<name>` first, then falls back to `queries.<name>`, then treats the value as raw SQL or `@file` when no named query exists.
4. **Supply parameters**: date variables and SQL bind parameters as extra `--key value` flags.
5. **Shape the output**: use `--first`, `--key`, `--value`, `--wrapper`, `--jsonkeys` to transform results.

---

## Discovery — orient before querying

Before calling a query, an agent can inspect what is configured:

```bash
# List available database connections
sql2json --list-connections --config /path/to/config.json
# → ["default", "mysql", "reporting"]

# List available named queries, grouped by scope
sql2json --list-queries --config /path/to/config.json
# → {"global": ["default", "sales_monthly"], "connections": {"mysql": ["table_sizes"], "reporting": ["total_users"]}}

# Request the old flat global-query list when integrating with legacy callers
sql2json --list-queries legacy --config /path/to/config.json
# → ["default", "sales_monthly"]
```

`--list-connections` prints a JSON array to stdout and exits 0. `--list-queries` prints the scoped discovery object by default; `--list-queries legacy` prints the old flat global query array. If `--config` is omitted the tool uses its normal config lookup order.

When selecting a named query for a connection, prefer a query listed under `connections.<connection>`; if none matches, use the matching name from `global`. Runtime lookup follows the same precedence: scoped query first, global query fallback, then raw SQL/`@file` behavior.

---

## Config file lookup order

When `--config` is not supplied, the tool searches in this order:

1. `./sql2json.json` (current working directory)
2. `./.sql2json/config.json` (current working directory)
3. `~/.sql2json/config.json` (user home directory)

If none exist, a read-only in-memory SQLite database is used (useful for testing).

---

## Config schema for named queries

Use top-level `queries` for shared/global named queries and `connection_queries` for connection-specific SQL. `connection_queries` is the canonical schema for scoped queries: connection name -> query name -> SQL.

```json
{
  "connections": {
    "postgres": "postgresql+psycopg2://user:pass@host/db",
    "mysql": "mysql+pymysql://user:pass@host/db"
  },
  "queries": {
    "sales": "SELECT month, amount FROM sales",
    "long_report": "@/path/to/report.sql"
  },
  "connection_queries": {
    "postgres": {
      "now": "SELECT CURRENT_TIMESTAMP AS ts"
    },
    "mysql": {
      "now": "SELECT NOW() AS ts"
    }
  }
}
```

Existing `queries` configs remain valid; they are the fallback/global scope. Query values may be raw SQL or `@/path.sql` file references.

---

## Key flags

| Flag | Purpose | Example |
|---|---|---|
| `--name` | Connection profile name in `config.json`, or a raw SQLAlchemy URL | `--name mysql` |
| `--query` | Named query in `config.json`, raw SQL string, or `@/path/file.sql` | `--query sales_monthly` |
| `--config` | Path to a specific config file | `--config /etc/sql2json/prod.json` |
| `--first` | Return only the first row instead of an array | `--first` |
| `--key` | Extract a single column as the value (scalar with `--first`) or use as dict key (with `--value`) | `--key sales` |
| `--value` | Use with `--key` to produce `{key_col: value_col}` dicts | `--value amount` |
| `--wrapper` | Wrap result in `{"data": [...]}` | `--wrapper` |
| `--jsonkeys` | Comma-separated columns whose string values should be parsed as JSON | `--jsonkeys payload,metadata` |
| `--format` | Output format: `json` (default), `csv`, `excel` | `--format csv` |
| `--output` | Save to file instead of printing; filename supports `{CURRENT_DATE}` etc. | `--output report_{CURRENT_DATE}` |
| `--list-connections` | Print JSON array of configured connection names and exit | `--list-connections` |
| `--list-queries` | Print configured query names and exit. Default shape is `{"global": [...], "connections": {...}}`; pass `--list-queries legacy` for the old flat global query array | `--list-queries` |

**Note:** Both `--list-connections` and `--list_connections` (underscore) are accepted by fire.

---

## Output formats for agents

Agents should use **JSON** (default) or **CSV** (`--format csv --output file`).

- JSON is returned on stdout and can be piped directly.
- CSV requires `--output` to write to a file.
- Excel (`--format excel`) is best for human consumption; agents should prefer JSON or CSV.

---

## Error handling

On failure, sql2json prints a JSON object to **stderr** and exits with a non-zero code. Stdout is empty on error.

```json
{"error": "no such table: orders", "type": "OperationalError"}
```

Agents should:
1. Check the exit code.
2. Parse stderr as JSON to get a structured error message.
3. Leave stdout handling unchanged (it is clean / empty on error).

---

## Date variables

Extra kwargs become SQL bind parameters (`:param_name` in the query). Values that match built-in variables are resolved before execution:

| Variable | Resolves to |
|---|---|
| `CURRENT_DATE` | Today's date |
| `START_CURRENT_MONTH` | First day of the current month |
| `END_CURRENT_MONTH` | Last day of the current month |
| `START_CURRENT_YEAR` | First day of the current year |
| `END_CURRENT_YEAR` | Last day of the current year |

**Arithmetic:** `CURRENT_DATE-7` (days), `START_CURRENT_MONTH+1` (months), `START_CURRENT_YEAR+1` (years).

**Custom format:** `CURRENT_DATE|%Y-%m-%d 00:00:00`

---

## CLI examples

```bash
# Run a named query with a date parameter
sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1"

# Run inline SQL directly
sql2json --name mysql --query "SELECT COUNT(*) AS total FROM orders WHERE date >= :since" --since "CURRENT_DATE-7"

# Return only the first row, extract a single column value
sql2json --name mysql --query total_sales --date_from "CURRENT_DATE-10" --first --key sales

# Return results as {key_col: value_col} pairs
sql2json --name mysql --query sales_monthly --key month --value sales

# Wrap in {"data": [...]} for downstream systems
sql2json --name mysql --query sales_monthly --wrapper

# Load query from a .sql file
sql2json --name mysql --query "@/path/to/my_query.sql" --min_age 18

# Save output to a dated CSV file
sql2json --name mysql --query sales_monthly --format csv --output sales_{CURRENT_DATE}
```

---

## Python API

```python
from sql2json import run_query2json, run_query_by_name, list_connections, list_queries

# Discover what's configured
connections = list_connections("/path/to/config.json")
queries = list_queries("/path/to/config.json")                         # global legacy names
scoped_queries = list_queries("/path/to/config.json", scoped=True)      # {"global": [...], "connections": {...}}
mysql_queries = list_queries("/path/to/config.json", connection="mysql")

# Run a named query — returns list of dicts
rows = run_query_by_name(
    conection_name="mysql",
    query_name="sales_monthly",
    date_from="START_CURRENT_MONTH-1",
    config="/path/to/config.json",
)

# Run with output transformations
result = run_query2json(
    name="mysql",
    query="SELECT SUM(amount) AS total FROM orders WHERE date >= :since",
    first=True,
    key="total",
    since="CURRENT_DATE-7",
    config="/path/to/config.json",
)

# Python API raises exceptions normally — no error envelope
```

`config` is a special kwarg handled by the library; it is not forwarded to SQLAlchemy as a bind parameter.

---

## Security

- Validate and scope any SQL before passing it to `--query`. The tool executes whatever SQL it receives.
- Use named queries from `config.json` when possible to limit the SQL surface.
- The tool does not enforce read-only access — that is the caller's responsibility.
