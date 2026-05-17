# sql2json

Run SQL queries and get JSON (or CSV) on stdout — pipe it anywhere.

`sql2json` connects to any SQLAlchemy-supported database, executes a query, and writes the results as JSON to standard output. No server, no framework, no boilerplate.

```bash
python -m sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1"
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
python -m sql2json
# → [{"a": 1, "b": 2}]
```

**3. Try inline SQL:**

```bash
python -m sql2json --name default --query "SELECT date('now') AS today"
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
python -m sql2json [options] [--param value ...]
```

| Flag | Default | Description |
|---|---|---|
| `--name` | `default` | Connection name from config, or a raw SQLAlchemy URL |
| `--query` | `default` | Named query, raw SQL string, or `@/path/file.sql` |
| `--config` | _(lookup order above)_ | Path to a specific config file |
| `--first` | `False` | Return only the first row (object, not array) |
| `--key` | `""` | Extract one column as value (scalar with `--first`), or dict key (with `--value`) |
| `--value` | `""` | Used with `--key` to produce `{key_col: value_col}` dicts |
| `--wrapper` | `False` | Wrap result in `{"data": [...]}` |
| `--jsonkeys` | `""` | Comma-separated columns whose string values should be parsed as JSON |
| `--format` | `json` | Output format: `json`, `csv`, `excel` |
| `--output` | _(stdout)_ | Save to file; filename supports `{CURRENT_DATE}` etc. |
| `--list-connections` | — | Print JSON array of configured connection names and exit |
| `--list-queries` | — | Print JSON array of configured query names and exit |

Extra `--key value` flags become SQL bind parameters (`:key` in your query).

### Discovery

Before writing a query, inspect what is configured:

```bash
python -m sql2json --list-connections
# → ["default", "mysql", "reporting"]

python -m sql2json --list-queries
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
python -m sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1"
```
```json
[
    {"month": "January", "sales": 5000},
    {"month": "February", "sales": 3000}
]
```

### First row only (`--first`)

```bash
python -m sql2json --name mysql --query total_sales --date_from "CURRENT_DATE-10" --first
```
```json
{"sales": 500}
```

### Single value (`--first --key`)

```bash
python -m sql2json --name mysql --query total_sales --date_from "CURRENT_DATE-10" --first --key sales
```
```
500
```

### Key-value pairs (`--key --value`)

```bash
python -m sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1" --key month --value sales
```
```json
[
    {"January": 5000},
    {"February": 3000}
]
```

### Wrapped for dashboards (`--wrapper`)

```bash
python -m sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1" --wrapper
```
```json
{
    "data": [
        {"month": "January", "sales": 5000},
        {"month": "February", "sales": 3000}
    ]
}
```

### Parse JSON columns (`--jsonkeys`)

When a column contains a JSON string from a database JSON function, use `--jsonkeys` to parse it:

```bash
python -m sql2json --name mysql --query json_report --jsonkeys "payload,metadata"
```

Without `--jsonkeys` those columns would be escaped strings; with it they are inlined as JSON.

### Inline SQL

No need to define every query in the config file:

```bash
python -m sql2json --name mysql --query "SELECT NOW() AS ts" --first --key ts
```

### External `.sql` file

```bash
# Defined in config.json as "@/path/to/file.sql"
python -m sql2json --name mysql --query long_query --min_age 18

# Or pass the path directly
python -m sql2json --name mysql --query "@/path/to/my_query.sql" --min_age 18
```

## File output

Use `--output` to write to a file instead of stdout. The `--format` flag controls the extension (default `json`):

```bash
# CSV file
python -m sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1" --format csv --output Sales
# → Sales.csv

# Excel file
python -m sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1" --format excel --output Sales
# → Sales.xls

# JSON file
python -m sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH-1" --format json --output Sales
# → Sales.json
```

**Dated filenames** — use date variables in `--output`:

```bash
python -m sql2json --name mysql --query sales_monthly --date_from "START_CURRENT_MONTH" \
    --format csv --output "Sales_{START_CURRENT_MONTH}_{CURRENT_DATE}"
# → Sales_2026-05-01_2026-05-16.csv

python -m sql2json --name mysql --query sales_monthly --date_from "CURRENT_DATE" \
    --format csv --output "reports/Sales_{CURRENT_DATE}"
# → reports/Sales_2026-05-16.csv
```

> **Note:** `--output` does not create directories. Create the target folder first.

> **Note:** CSV requires `--output` (it cannot be written to stdout).

## For AI agents

`sql2json` is designed to be called as a subprocess by AI agents and LLMs. It outputs clean JSON to stdout, structured errors to stderr, and supports discovery commands so an agent can orient itself before querying.

See [AGENTS.md](AGENTS.md) for the full agent integration guide, including discovery flags, error handling, the Python API, and security notes.
