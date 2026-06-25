import datetime
import json
import os
import sys
from typing import Optional, Union
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.sql import text

from .parameter import parse_parameter


def _current_date(timezone: Optional[str] = None) -> datetime.date:
    if timezone:
        return datetime.datetime.now(ZoneInfo(timezone)).date()
    return datetime.date.today()


def map_result_proxy2list_dict(result_proxy) -> list:
    keys = list(result_proxy.keys())
    return [dict(zip(keys, row)) for row in result_proxy]


_TRUTHY_STRINGS = {"true", "t", "yes", "y", "1", "on"}


def _coerce_bool(value) -> bool:
    """
    Coerce a CLI/string value to a bool.

    fire passes a bare flag (``--read-only``) as ``True`` but a value form
    (``--read-only yes``) through as the string ``"yes"``; this normalizes both,
    accepting ``true``/``t``/``yes``/``y``/``1``/``on`` (case-insensitive) as true.
    """
    if isinstance(value, str):
        return value.strip().lower() in _TRUTHY_STRINGS
    return bool(value)


def _begin_read_only(con) -> None:
    """
    Best-effort: put the live connection into a real read-only transaction where
    the backend supports it, so a write is rejected by the database *before* it
    runs (no triggers, no side effects). Verified on SQLite and PostgreSQL;
    other backends are caught by the unconditional rollback in run_query, which
    is the portable backstop, so any failure here is intentionally swallowed.
    """
    dialect = con.engine.dialect.name
    try:
        if dialect == "sqlite":
            con.exec_driver_sql("PRAGMA query_only = ON")
        elif dialect in ("postgresql", "mysql", "mariadb"):
            con.exec_driver_sql("SET TRANSACTION READ ONLY")
    except Exception:
        pass


def _is_read_only_violation(exc: Exception) -> bool:
    """True when a database error is a read-only / write-blocked rejection."""
    message = str(getattr(exc, "orig", exc)).lower()
    return "readonly" in message or "read only" in message or "read-only" in message


def run_query(
    engine,
    raw_query: str,
    timezone: Optional[str] = None,
    read_only: bool = False,
    **kwargs,
) -> Union[list, dict]:
    """
    Execute a single SQL statement and return its result.

    Row-returning statements (SELECT, ``... RETURNING``) yield a list of dicts.
    Statements that return no rows (INSERT / UPDATE / DELETE without RETURNING,
    DDL) yield ``{"rowcount": N}`` instead of raising. ``returns_rows`` is used
    to tell the two apart — more robust than sniffing the SQL string.

    Writes are committed by default (autocommit). When ``read_only`` is true the
    statement runs without persisting: a real read-only transaction is requested
    where the backend supports it (SQLite/PostgreSQL/MySQL) so a write is
    rejected up front, and the transaction is *always* rolled back as a portable
    backstop. A rejected write is reported as ``{"rowcount": 0}`` rather than
    raising, so read-only mode never hard-fails on a write.
    """
    read_only = _coerce_bool(read_only)
    current_date = _current_date(timezone)
    parameters = {k: parse_parameter(v, current_date) for k, v in kwargs.items()}

    with engine.connect() as con:
        if read_only:
            _begin_read_only(con)

        try:
            result_proxy = con.execute(text(raw_query), parameters)

            if result_proxy.returns_rows:
                records: Union[list, dict] = map_result_proxy2list_dict(result_proxy)
            else:
                # Clamp to 0 for a consistent contract across drivers: a DDL /
                # "count unknown" statement reports -1 on SQLite/PostgreSQL but 0
                # on MySQL, so normalize any non-positive value to 0. Real DML
                # affected-row counts are >= 1 and pass through unchanged.
                records = {"rowcount": max(result_proxy.rowcount, 0)}
        except Exception as exc:
            # Real read-only guard: the database rejected the write. Surface the
            # same soft "nothing persisted" result as the rollback fallback
            # instead of a hard error.
            if read_only and _is_read_only_violation(exc):
                con.rollback()
                return {"rowcount": 0}
            raise
        finally:
            # PRAGMA query_only is connection-scoped; clear it so a pooled
            # SQLite connection is not left read-only for later reuse.
            if read_only and con.engine.dialect.name == "sqlite":
                try:
                    con.exec_driver_sql("PRAGMA query_only = OFF")
                except Exception:
                    pass

        if read_only:
            con.rollback()
        else:
            con.commit()

    return records


def load_config_file(config_path: str) -> dict:
    try:
        with open(config_path) as json_file:
            return json.load(json_file)
    except Exception:
        pass

    return {
        "conections": {"default": "sqlite:///:memory:"},
        "queries": {"default": "SELECT 1 AS a, 2 AS b"},
    }


def _find_config() -> str:
    """
    Return the first config file found using this lookup order:
      1. ./sql2json.json
      2. ./.sql2json/config.json
      3. ~/.sql2json/config.json  (may not exist — load_config_file falls back to
                                   an in-memory test DB when the file is missing)
    """
    candidates = [
        os.path.join(os.getcwd(), "sql2json.json"),
        os.path.join(os.getcwd(), ".sql2json", "config.json"),
        os.path.join(os.path.expanduser("~"), ".sql2json", "config.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[-1]


def load_query_from_file(sql_file_path: str) -> str:
    file_name = sql_file_path

    if sql_file_path.startswith("@"):
        file_name = sql_file_path[1:]

    with open(file_name, "r") as file:
        return file.read()


def get_for_key_or_first_map_value(my_dict: dict, key: Optional[str] = None):
    if key in my_dict:
        return my_dict.get(key)

    for _, v in my_dict.items():
        return v

    return ""


def _get_connections_dict(config: dict) -> dict:
    """Return the connections dict, accepting both 'connections' and 'conections'."""
    return config.get("connections") or config.get("conections", {})


def list_connections(config_path: Optional[str] = None) -> list:
    """Return the names of all configured database connections."""
    path = config_path or _find_config()
    config = load_config_file(path)
    return list(_get_connections_dict(config).keys())


def list_queries(
    config_path: Optional[str] = None,
    scoped: bool = False,
    connection: Optional[str] = None,
) -> Union[list, dict]:
    """
    Return configured query names.

    By default this preserves the historical public API and returns only global
    query names from the top-level ``queries`` object.

    When ``scoped`` is true, return an agent-friendly discovery object that
    separates top-level global queries from per-connection scoped queries::

        {"global": [...], "connections": {"connection_name": [...]}}

    When ``connection`` is provided, return the effective query names for that
    connection: global query names plus connection-scoped names, with scoped
    names appearing only once when they shadow a global query of the same name.
    """
    path = config_path or _find_config()
    config = load_config_file(path)
    global_query_names = list(config.get("queries", {}).keys())

    if not scoped and connection is None:
        return global_query_names

    connections = _get_connections_dict(config)
    connection_queries = _get_connection_queries_dict(config, connections)

    if scoped:
        return {
            "global": global_query_names,
            "connections": {
                connection_name: list(queries.keys())
                for connection_name, queries in connection_queries.items()
            },
        }

    if connection is not None:
        effective_query_names = list(global_query_names)
        for query_name in connection_queries.get(connection, {}).keys():
            if query_name not in effective_query_names:
                effective_query_names.append(query_name)
        return effective_query_names

    return global_query_names


def _get_connection_queries_dict(config: dict, connections: dict) -> dict:
    """Return validated per-connection query mappings from config."""
    connection_queries = config.get("connection_queries", {})

    if connection_queries is None:
        return {}

    if not isinstance(connection_queries, dict):
        raise ValueError("connection_queries must be an object")

    for connection_name, queries in connection_queries.items():
        if connection_name not in connections:
            raise ValueError(
                f"connection_queries references unknown connection '{connection_name}'"
            )

        if not isinstance(queries, dict):
            raise ValueError(f"connection_queries.{connection_name} must be an object")

        for query_name, raw_query in queries.items():
            if not isinstance(raw_query, str):
                raise ValueError(
                    f"connection_queries.{connection_name}.{query_name} must be a string"
                )

    return connection_queries


def _resolve_query_string(
    connection_name: str, query_name: str, connections: dict, config: dict
) -> str:
    connection_queries = _get_connection_queries_dict(config, connections)
    scoped_queries = connection_queries.get(connection_name, {})

    if connection_name in connections and query_name in scoped_queries:
        return scoped_queries[query_name]

    config_queries = config.get("queries", {})
    return config_queries.get(query_name, query_name)


def run_query_by_name(
    conection_name: str = "default", query_name: str = "default", **kwargs
) -> Union[list, dict]:
    """
    Run a SQL query given a conection_name, query_name.

    Returns a list of dicts for row-returning statements, or ``{"rowcount": N}``
    for statements that return no rows. Writes commit by default; pass
    ``read_only=True`` to roll back instead (the statement still runs).
    """
    # Pop config, timezone and read_only before passing kwargs to SQLAlchemy so they aren't treated as bind params
    config_path = kwargs.pop("config", None) or _find_config()
    timezone = kwargs.pop("timezone", None)
    read_only = kwargs.pop("read_only", False)

    config = load_config_file(config_path)

    config_dbs = _get_connections_dict(config)

    # If conection_name does not exist, try to use as connection string
    conection_string = config_dbs.get(conection_name, conection_name)

    raw_query_string = _resolve_query_string(
        conection_name, query_name, config_dbs, config
    )

    if raw_query_string.startswith("@"):
        raw_query_string = load_query_from_file(raw_query_string[1:])

    engine = create_engine(conection_string)

    return run_query(
        engine, raw_query_string, timezone=timezone, read_only=read_only, **kwargs
    )


def parse_json_columns(result: dict, jsonkeys: str = "") -> dict:
    """
    Convert string-encoded JSON columns to parsed objects.
    jsonkeys: comma-separated column names whose values should be parsed as JSON.
    """
    jsonkeys_list = []

    if type(jsonkeys) is tuple:
        jsonkeys_list = [key.strip() for key in jsonkeys]
    elif type(jsonkeys) is str:
        jsonkeys_list = [key.strip() for key in jsonkeys.split(",")]

    if not jsonkeys_list:
        return result

    response = {}

    for key in result:
        if key in jsonkeys_list:
            response[key] = json.loads(result[key])
        else:
            response[key] = result[key]

    return response


def apply_wrapper(
    result: Union[str, dict, list], wrapper: Union[bool, str] = False
) -> Union[str, dict, list]:
    """
    Wrap a result under a top-level key.

    A non-empty string wraps under that key (e.g. "items" -> {"items": ...});
    True wraps under "data" ({"data": ...}); False or "" returns it unwrapped.
    """
    if isinstance(wrapper, str) and wrapper:
        return {wrapper: result}
    elif wrapper:
        return {"data": result}
    return result


def apply_output_transforms(
    unparsed_results: list,
    wrapper: Union[bool, str] = False,
    first: bool = False,
    key: str = "",
    value: str = "",
    jsonkeys: str = "",
) -> Union[str, dict, list]:
    """
    Apply the row-shaping (first/key/value/jsonkeys) and wrapper transforms to a
    list of row dicts. Shared by both the read (``query``) and write (``execute``)
    code paths so row-returning output is identical across commands.
    """
    results = [parse_json_columns(result, jsonkeys) for result in unparsed_results]

    result: Union[str, dict, list, None] = None

    if first:
        if results and len(results) > 0:
            item = results[0]

            if key and value:
                result = {item.get(key): item.get(value)}
            else:
                result = get_for_key_or_first_map_value(item, key) if key else item
        else:
            result = "" if key and not value else {}
    else:
        if key and value:
            result = [
                (
                    {item.get(key): item.get(value)}
                    if key and key in item and value in item
                    else item
                )
                for item in results
            ]
        else:
            result = [
                item.get(key) if key and key in item else item for item in results
            ]

    return apply_wrapper(result, wrapper)


def _warn_read_only_write(result: dict) -> None:
    """
    Print a friendly notice (on stderr, so stdout stays clean JSON) when a write
    statement is run under ``--read-only``. The write is never persisted — it is
    rejected by the database where supported, and always rolled back as a
    backstop — so this replaces the old hard failure with a clear explanation.
    """
    print(
        "read-only mode: write not persisted "
        "(re-run without --read-only to commit the change).",
        file=sys.stderr,
    )


def run_query2json(
    name: str = "default",
    query: str = "default",
    wrapper: Union[bool, str] = False,
    first: bool = False,
    key: str = "",
    value: str = "",
    jsonkeys: str = "",
    timezone: Optional[str] = None,
    read_only: bool = False,
    **kwargs,
) -> Union[str, dict, list]:
    """
    Run a SQL statement and return results with optional transformations.

    Writes commit by default (autocommit): an INSERT / UPDATE / DELETE / DDL
    statement persists and returns ``{"rowcount": N}``, while SELECT /
    ``... RETURNING`` return rows shaped by the transform flags. Pass
    ``read_only=True`` to roll the statement back instead — it still executes but
    nothing is persisted, and a notice is printed to stderr for write statements.

    name: Connection name in config file or a SQLAlchemy connection string.
    query: Query name in config file, raw SQL, or @/path/to/file.sql.
    wrapper: Wrap result. True wraps under "data" ({"data": ...}); a non-empty
        string wraps under that key (e.g. "items" -> {"items": ...}); False or ""
        returns the result unwrapped.
    first: Return only the first row.
    key: Column name to use as key (with value) or extract as scalar (with first).
    value: Column name to use as value (used with key).
    jsonkeys: Comma-separated columns whose string values should be parsed as JSON.
    timezone: IANA timezone name used to resolve CURRENT_DATE and related variables (e.g. "America/New_York"). Defaults to local system timezone.
    read_only: When true, roll back instead of committing (statement still runs).
    """
    read_only = _coerce_bool(read_only)
    result = run_query_by_name(
        name, query, timezone=timezone, read_only=read_only, **kwargs
    )

    # A non-row-returning statement (INSERT / UPDATE / DELETE / DDL) comes back
    # as {"rowcount": N}; row shaping does not apply, but the wrapper still does.
    if isinstance(result, dict):
        if read_only:
            _warn_read_only_write(result)
        return apply_wrapper(result, wrapper)

    return apply_output_transforms(result, wrapper, first, key, value, jsonkeys)
