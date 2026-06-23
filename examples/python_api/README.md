# Python API examples

These examples show how to use the supported `sql2json` Python API without relying on private implementation details.

Run from the repository root with:

```bash
uv run python examples/python_api/run_inline_sql.py
uv run python examples/python_api/output_shapes.py
uv run python examples/python_api/list_config.py
uv run python examples/python_api/run_named_query.py
uv run python examples/python_api/json_columns.py
uv run python examples/python_api/date_parameters.py
uv run python examples/python_api/sql_file.py
uv run python examples/python_api/error_handling.py
```

Public API used here:

- `run_query2json`
- `run_query_by_name`
- `list_connections`
- `list_queries`
- `parse_parameter`

`list_queries(path)` returns legacy global query names. Use `list_queries(path, scoped=True)` to return the full discovery shape (`{"global": [...], "connections": {...}}`), or `list_queries(path, connection="name")` to get the effective names for one connection, including connection-scoped queries and global fallbacks.

Implementation helpers inside `sql2json.sql2json`, `sql2json.__main__`, or `sql2json.parameter.parameter_parser` are internal and should not be imported by users.
