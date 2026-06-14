---
name: sql2json
description: Use when you need to query a SQL database from the terminal with sql2json, especially for live repo DB checks, named queries from ~/.sql2json/config.json, or quick JSON/CSV output from SQLAlchemy-backed connections.
version: 1.0.0
author: Francisco + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [sql, database, cli, sqlite, postgres, mysql, json, csv, sql2json]
---

# sql2json

## Overview

`sql2json` is a lightweight CLI that runs SQLAlchemy-supported queries and prints JSON, CSV, or Excel output directly to stdout or a file. It works with any project — there is no built-in assumption about which database or schema you are using.

Install once, use from any project:

```bash
pip install sql2json
```

## When to Use

Use this skill when you need to:

- Run a named query from `~/.sql2json/config.json`
- Execute a one-off SQL statement and get JSON back quickly
- Pipe database results into `jq`, scripts, or other CLI tools
- Export query results as CSV or Excel

Don't use this skill when:

- You need to mutate data without a clear query
- You already have a dedicated app-level API that exposes the answer
- The target database is not reachable

## Setup

The config file lives at `~/.sql2json/config.json`. Create it with at least one named connection and, optionally, named queries:

```json
{
    "connections": {
        "mydb": "postgresql+psycopg2://user:password@localhost/mydb"
    },
    "queries": {
        "users": "SELECT id, email FROM users LIMIT 10"
    }
}
```

Supported connection strings follow SQLAlchemy format:

| Database   | Example connection string |
|---|---|
| SQLite     | `sqlite:////path/to/db.sqlite` |
| PostgreSQL | `postgresql+psycopg2://user:pass@host/db` |
| MySQL      | `mysql+pymysql://user:pass@host/db` |
| MS SQL     | `mssql+pyodbc://user:pass@host/db?driver=ODBC+Driver+17+for+SQL+Server` |

Discover what is configured:

```bash
sql2json --list-connections
sql2json --list-queries
```

## Common query patterns

**Named query:**

```bash
sql2json --name mydb --query users
```

**Inline SQL:**

```bash
sql2json --name mydb --query 'SELECT COUNT(*) AS n FROM users' --first --key n
```

**Parameterized SQL:**

```bash
sql2json --name mydb --query 'SELECT * FROM orders WHERE status = :status' --status confirmed
```

**Date variables** (resolved at runtime):

```bash
sql2json --name mydb --query 'SELECT * FROM events WHERE created_at >= :from_date' \
  --from_date START_CURRENT_MONTH
```

Available variables: `CURRENT_DATE`, `START_CURRENT_MONTH`, `END_CURRENT_MONTH`, `START_CURRENT_YEAR`, `END_CURRENT_YEAR`. Supports arithmetic (`CURRENT_DATE-7`) and custom formats (`CURRENT_DATE|%Y-%m-%d 00:00:00`).

**CSV output:**

```bash
sql2json --name mydb --query users --format csv --output /tmp/users.csv
```

**Excel output:**

```bash
sql2json --name mydb --query users --format excel --output /tmp/users.xlsx
```

**Extract a single value:**

```bash
sql2json --name mydb --query 'SELECT COUNT(*) AS n FROM users' --first --key n
# → 42
```

**Key/value dict:**

```bash
sql2json --name mydb --query 'SELECT id, name FROM users' --key id --value name
# → {"1": "Alice", "2": "Bob"}
```

## Docker

Run without installing anything locally:

```bash
# Quick test (built-in SQLite fallback — no config needed)
docker run --rm sql2json --query "SELECT 1 AS a, 2 AS b"

# With your config
docker run --rm -v ~/.sql2json:/root/.sql2json \
  sql2json --name mydb --query users
```

## Sync strategy

This skill is designed to be shared across AI agents. Keep the canonical copy in your project repository and symlink it from each agent's skill directory so a single edit propagates everywhere.

Canonical location in the sql2json repo:

```text
skills/sql2json/SKILL.md
```

Run the install script from the repo root to set up all symlinks:

```bash
./scripts/install-skills.sh
```

Supported agent targets:

| Agent  | Target path |
|---|---|
| Hermes | `~/.hermes/skills/productivity/sql2json/SKILL.md` |
| Claude | `~/.claude/skills/sql2json/SKILL.md` |

See `references/agent-sync.md` for the full agent-target map.

## Pitfalls

1. `sql2json` writes errors to stderr. Check the exit code and stderr, not just stdout.
2. Named queries come from `~/.sql2json/config.json`; a missing query name is a config problem, not a skill problem.
3. `Decimal` columns are serialized as floats. `date`/`datetime` columns are not handled natively — cast to `VARCHAR` in SQL or use `--jsonkeys` if the driver returns them as strings.
4. Keep the canonical file in the repo; do not hand-edit copies in agent-local skill directories.

## Verification checklist

- [ ] `sql2json` is on PATH (`which sql2json`)
- [ ] `~/.sql2json/config.json` contains the expected connection name
- [ ] `sql2json --list-connections` shows the expected connections
- [ ] `sql2json --name <conn> --query '<SQL>'` returns JSON as expected
- [ ] Agent-local skill files are symlinks to the canonical copy, not divergent files
