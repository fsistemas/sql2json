# Using `sql2json` with AI Agents and LLMs

`sql2json` runs SQL queries via SQLAlchemy and outputs JSON or CSV to stdout. It is invoked as a CLI tool or imported as a Python package — no framework coupling, no MCP server required.

---

## Strategy for Agents

Map a natural language request to these parameters:

1. **Identify the connection** (`--name`): which database to use.
2. **Select the query** (`--query`): a named query from `config.json`, raw inline SQL, or a path to a `.sql` file prefixed with `@`.
3. **Supply parameters**: date variables and SQL bind parameters as extra `--key value` flags.
4. **Shape the output**: use `--first`, `--key`, `--value`, `--wrapper`, `--jsonkeys` to transform results.

---

## Discovery — orient before querying

Before calling a query, an agent can inspect what is configured:

```bash
# List available database connections
python -m sql2json --list-connections --config /path/to/config.json
# → ["default", "mysql", "reporting"]

# List available named queries
python -m sql2json --list-queries --config /path/to/config.json
# → ["default", "sales_monthly", "total_users"]
```

Both flags print a JSON array to stdout and exit 0. If `--config` is omitted the tool uses its normal config lookup order.

---

## Config file lookup order

When `--config` is not supplied, the tool searches in this order:

1. `./sql2json.json` (current working directory)
2. `./.sql2json/config.json` (current working directory)
3. `~/.sql2json/config.json` (user home directory)

If none exist, a read-only in-memory SQLite database is used (useful for testing).

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
| `--list-queries` | Print JSON array of configured query names and exit | `--list-queries` |

**Note:** Both `--list-connections` and `--list_connections` (underscore) are accepted by fire.

---

## Output formats for agents

Agents should use **JSON** (default) or **CSV** (`--format csv --output file`).

- JSON is returned on stdout and can be piped directly.
- CSV requires `--output` to write to a file.
- Excel (`--format excel`) is available for human consumption only.

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
python -m sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1"

# Run inline SQL directly
python -m sql2json --name mysql --query "SELECT COUNT(*) AS total FROM orders WHERE date >= :since" --since "CURRENT_DATE-7"

# Return only the first row, extract a single column value
python -m sql2json --name mysql --query total_sales --date_from "CURRENT_DATE-10" --first --key sales

# Return results as {key_col: value_col} pairs
python -m sql2json --name mysql --query sales_monthly --key month --value sales

# Wrap in {"data": [...]} for downstream systems
python -m sql2json --name mysql --query sales_monthly --wrapper

# Load query from a .sql file
python -m sql2json --name mysql --query "@/path/to/my_query.sql" --min_age 18

# Save output to a dated CSV file
python -m sql2json --name mysql --query sales_monthly --format csv --output sales_{CURRENT_DATE}
```

---

## Python API

```python
from sql2json import run_query2json, run_query_by_name, list_connections, list_queries

# Discover what's configured
connections = list_connections("/path/to/config.json")  # ["default", "mysql"]
queries = list_queries("/path/to/config.json")          # ["default", "sales_monthly"]

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
