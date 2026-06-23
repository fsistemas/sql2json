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

Install once as an isolated tool, **with the Postgres and MySQL drivers
bundled**, and use it from any project:

```bash
uv tool install "sql2json[postgres,mysql]"
# or
pipx install "sql2json[postgres,mysql]"
```

These methods work on **externally-managed** systems (Manjaro/Arch, Debian 12+,
Ubuntu 23.04+, Homebrew Python), where a bare `pip install` is refused with
`error: externally-managed-environment` ([PEP 668](https://peps.python.org/pep-0668/)),
and they put `sql2json` on `PATH` without touching project environments.

**Quote the extras** — in bash/zsh the brackets are glob characters, so
`"sql2json[postgres,mysql]"` must be quoted (PowerShell:
`'sql2json[postgres,mysql]'`). Bare `sql2json` is **SQLite only**; add
`[postgres]` and/or `[mysql]` for those databases (other drivers, e.g. `pyodbc`
for MS SQL, install alongside). For library/project use, add it as a dependency
instead: `uv add "sql2json[postgres,mysql]"` or, in a venv,
`pip install "sql2json[postgres,mysql]"`.

**Upgrade** (keep the extras so drivers stay installed):

```bash
uv tool upgrade sql2json      # or: uv tool install "sql2json[postgres,mysql]" --force
pipx upgrade sql2json
pip install --upgrade "sql2json[postgres,mysql]"   # inside a venv
```

Examples here use the `sql2json` command, available since **v0.2.1**. On `0.2.0`
and earlier — or if the command is not on `PATH` — use the equivalent
`python -m sql2json ...` form instead (on Windows, `py -m sql2json ...`).

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
    },
    "connection_queries": {
        "mydb": {
            "table_sizes": "SELECT schemaname, relname, pg_total_relation_size(relid) AS bytes FROM pg_catalog.pg_statio_user_tables"
        }
    }
}
```

Use `queries` for shared/global named queries. Use optional `connection_queries` as the canonical schema for connection-specific SQL: connection name -> query name -> SQL. Existing configs that omit `connection_queries` remain valid, and global `queries` act as fallbacks.

Named query resolution is: `connection_queries.<connection>.<query>` first, then `queries.<query>`, then raw SQL or `@/path.sql` handling.

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
# → {"global": ["users"], "connections": {"mydb": ["table_sizes"]}}
sql2json --list-queries legacy   # old flat global query list
```

When an agent receives a data request, discover connections and scoped queries before inventing SQL. Choose a connection, then prefer a query listed under that connection; fall back to a global query only if no scoped query matches.

## Common query patterns

**Named query:**

```bash
sql2json --name mydb --query users
```

**Connection-scoped named query:**

```bash
# Resolves to connection_queries.mydb.table_sizes before checking global queries.table_sizes
sql2json --name mydb --query table_sizes
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

**Wrap rows under a top-level key** (handy for dashboard/API payloads):

```bash
sql2json --name mydb --query users --wrapper          # → {"data": [...]}
sql2json --name mydb --query users --wrapper items     # → {"items": [...]}
```

`--wrapper` (bare) wraps under `"data"`; pass a name (`--wrapper items`) to wrap under that key instead. Omit it for a bare array.

## Docker

Run the official multi-arch image without installing anything locally. The image
is published on Docker Hub at <https://hub.docker.com/r/fsistemas/sql2json> as
`docker.io/fsistemas/sql2json` for `linux/amd64` and `linux/arm64`.

```bash
# Quick test (built-in SQLite fallback — no config needed)
podman run --rm docker.io/fsistemas/sql2json --query "SELECT 1 AS a, 2 AS b"
# → [{"a": 1, "b": 2}]

# Docker equivalent
docker run --rm docker.io/fsistemas/sql2json --query "SELECT 1 AS a, 2 AS b"

# Pin a production/CI release instead of using latest
podman pull docker.io/fsistemas/sql2json:0.3.0
```

The container runs as the unprivileged `app` user and reads config from
`/home/app/.sql2json`:

```bash
podman run --rm -v ~/.sql2json:/home/app/.sql2json \
  docker.io/fsistemas/sql2json --name mydb --query users
```

For release publishing from an amd64 maintainer machine, the known working
multi-arch path is rootful Podman with host-level QEMU/binfmt:

```bash
sudo podman run --rm --platform linux/arm64 --pull=always \
  docker.io/library/alpine uname -m   # must print: aarch64
sudo podman build --platform linux/amd64,linux/arm64 --pull=always \
  --build-arg VERSION=0.3.0 \
  --manifest docker.io/fsistemas/sql2json:0.3.0 .
sudo podman manifest push docker.io/fsistemas/sql2json:0.3.0 \
  docker.io/fsistemas/sql2json:0.3.0
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
3. For named queries, always account for scoped-query precedence: `connection_queries.<connection>.<query>` overrides the same name in global `queries`.
4. `Decimal` columns are serialized as floats. `date`/`datetime` columns are not handled natively — cast to `VARCHAR` in SQL or use `--jsonkeys` if the driver returns them as strings.
5. Keep the canonical file in the repo; do not hand-edit copies in agent-local skill directories.

## Verification checklist

- [ ] `sql2json` is on PATH (`which sql2json`)
- [ ] `~/.sql2json/config.json` contains the expected connection name
- [ ] `sql2json --list-connections` shows the expected connections
- [ ] `sql2json --name <conn> --query '<SQL>'` returns JSON as expected
- [ ] Agent-local skill files are symlinks to the canonical copy, not divergent files
