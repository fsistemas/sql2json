# sql2json Agent Readiness Roadmap

## Guiding principle

Keep everything that already works. Agents use the same CLI and Python API as humans — no new surfaces, no parallel API. Every change is either additive (new flags, new exports) or fixes something that was already broken.

---

## Prerequisites — bugs to fix first

These must be resolved before any agent work is meaningful.

### P0-A: Fix `pyproject.toml` build backend

`build-backend = "uv.build"` is not a real backend — `uv sync` fails with a Rust compiler error because it tries to build maturin. Should be `hatchling` or `setuptools`.

**Impact:** `uv sync` is broken for anyone who clones the repo. The published PyPI package was built differently and is fine, but local development and CI are blocked.

### P0-B: Fix SQLAlchemy 2.x row API

`map_result_proxy2list_dict()` calls `row.keys()` which is SQLAlchemy 1.x behavior. In SQLAlchemy 2.x `row.keys()` is a column name method on the result, not on individual rows. The uv.lock pins SQLAlchemy 2.x, creating a mismatch.

**Fix:** `[dict(row._mapping) for row in result_proxy]` works on SQLAlchemy 2.x and the result_proxy needs to be iterated before the connection closes (use `result_proxy.all()`).

**Impact:** The tool silently fails when run against the locked dependency version.

---

## Phase 1 — Make the CLI agent-friendly (additive only)

### 1.1 Structured errors on stderr

**Current behavior:** Python traceback to stderr, empty stdout, exit code 1.

**Problem for agents:** Tracebacks are not machine-parseable. An agent reading stderr gets a wall of Python stack frames with no reliable structure.

**Change:** Wrap the entire `handle_run_query2json()` call in a try/except. On failure, print a single JSON line to stderr and exit 1. Stdout stays empty on error (clean for pipes).

```
stderr → {"error": "No such table: orders", "type": "OperationalError"}
exit code → 1
```

**Backward compatible:** stderr content was never part of the contract (it was random tracebacks). stdout behavior is unchanged. Exit codes unchanged.

### 1.2 Discovery flags

Two new additive flags that output JSON to stdout and exit 0.

```bash
python -m sql2json --list-connections
# → ["default", "mysql", "postgres"]

python -m sql2json --list-queries
# → ["default", "sales_monthly", "total_sales"]
```

Both respect `--config` to load from a specific config file.

Agents use these to orient themselves before calling `--query`. Without them, an agent must be told out-of-band what connections and queries exist.

### 1.3 Config lookup order (add current-folder step)

**Current behavior:** `--config` flag OR `~/.sql2json/config.json`. No current-folder lookup.

**Target order:**
1. `--config` / `config=` kwarg (explicit)
2. `./sql2json.json` in the current working directory
3. `./.sql2json/config.json` in the current working directory
4. `~/.sql2json/config.json` (existing fallback)
5. In-memory SQLite test config (existing last resort)

**Backward compatible:** Existing behavior is preserved. New steps 2–3 only fire when no explicit config is given and the home-dir file doesn't exist yet.

---

## Phase 2 — Python API (clean up what already exists)

The functional API is already exported from `__init__.py` and works for both human and agent use. No new class is needed. The work here is additive exports and correctness.

### 2.1 Export discovery functions

```python
from sql2json import list_connections, list_queries

list_connections(config_path=None)  # → ["default", "mysql"]
list_queries(config_path=None)      # → ["default", "sales_monthly"]
```

These are just the internals of Phase 1.2 exposed as importable functions.

### 2.2 Type hints on public API

Add type annotations to `run_query2json()`, `run_query_by_name()`, `list_connections()`, `list_queries()`. Helps LLMs that inspect source or docstrings to understand expected types without guessing.

No signature changes. Pure annotation pass.

### 2.3 No new class

`run_query2json()` is already stateless and importable. A `Sql2Json` class would duplicate what already exists and create two ways to do the same thing. Dropped.

---

## Phase 3 — Fix AGENTS.md (corrections only)

Remove or correct factual errors. No structural rewrite.

**Errors to fix:**
- `--description` flag — does not exist. Inline SQL goes in `--query "SELECT ..."`.
- `--format dict` — does not exist. Key-value output uses `--key col1 --value col2`.
- Any output shape examples that don't match actual behavior.

**Add (since it didn't exist when AGENTS.md was written):**
- `--list-connections` / `--list-queries` examples
- Python API usage with `run_query2json()`
- Explicit note that Excel is not part of the agent interface (JSON and CSV only)
- Corrected config lookup order

---

## Out of scope

| Topic | Decision |
|---|---|
| MCP server | No |
| `Sql2Json` convenience class | No — functional API is enough |
| Framework adapters (LangChain, etc.) | No |
| Read-only SQL enforcement | No |
| `SQL2JSON_CONFIG` env var | No — `--config` flag covers it |
| Excel in agent interface | No — human/automation use only |

---

## Open questions (needs your call before implementation)

| Question | Options |
|---|---|
| Should `--list-connections` / `--list-queries` require a valid connection, or just read the config file? | Just read config (no DB ping) is simpler and safer. |
| Should the `--name` param accept a raw SQLAlchemy connection string as a fallback (it already does — is this documented for agents)? | Already works. Just needs to appear in AGENTS.md. |
