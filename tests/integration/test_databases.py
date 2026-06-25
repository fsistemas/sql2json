"""Real-database integration tests for the documented demo paths.

Covers, for both PostgreSQL and MySQL: named connection lookup, named query
lookup, bind parameters, numeric/Decimal values, end-to-end JSON serialization
through the CLI, and the write path — autocommit persistence and `--read-only`
rejection via `SET TRANSACTION READ ONLY` (the branch the SQLite unit tests
cannot exercise). Marked `integration` (deselected by default); see
tests/integration/conftest.py for provisioning and clean-skip behavior.
"""

import json
import os
import subprocess
import sys
from decimal import Decimal

import pytest

from sql2json import run_query2json
from sql2json.__main__ import json_dumps

pytestmark = pytest.mark.integration

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def run_cli(*args):
    env = {**os.environ, "PYTHONPATH": PROJECT_DIR}
    return subprocess.run(
        [sys.executable, "-m", "sql2json"] + list(args),
        capture_output=True,
        text=True,
        env=env,
    )


def test_named_connection_and_query_version(database):
    """Named connection + named `version` query returns one row of server text."""
    rows = run_query2json(database["name"], "version", config=database["config"])
    assert len(rows) == 1
    assert isinstance(rows[0]["version"], str)
    assert rows[0]["version"]


def test_named_query_sales_returns_seed_rows(database):
    """Named `sales` query returns the three seed rows with exact Decimal amounts."""
    rows = run_query2json(database["name"], "sales", config=database["config"])
    by_month = {r["month"]: r["amount"] for r in rows}
    assert len(rows) == 3
    assert by_month["January"] == Decimal("5000.00")
    assert by_month["February"] == Decimal("3200.50")
    assert by_month["March"] == Decimal("7100.75")


def test_numeric_values_are_decimal(database):
    """DECIMAL columns come back as Decimal from both drivers."""
    rows = run_query2json(database["name"], "sales", config=database["config"])
    assert all(isinstance(r["amount"], Decimal) for r in rows)


def test_bind_parameter_filters_rows(database):
    """`:min_amount` bind parameter filters server-side."""
    rows = run_query2json(
        database["name"], "sales_by_month", config=database["config"], min_amount=5000
    )
    assert sorted(r["month"] for r in rows) == ["January", "March"]


def test_json_dumps_handles_decimal(database):
    """Library-level serialization turns Decimal into JSON without raising."""
    rows = run_query2json(database["name"], "sales", config=database["config"])
    assert json.loads(json_dumps(rows))[0]["amount"] == 5000.0


def test_cli_json_serialization_decimal_to_float(database):
    """End-to-end CLI run emits valid JSON with Decimal rendered as float."""
    result = run_cli(
        "--name", database["name"], "--query", "sales", "--config", database["config"]
    )
    assert result.returncode == 0, result.stderr
    by_month = {r["month"]: r["amount"] for r in json.loads(result.stdout)}
    assert by_month["January"] == 5000.0
    assert isinstance(by_month["January"], float)


# Table used by the write tests; created/dropped per test so the shared demo
# database is left clean and tests do not depend on ordering.
_WRITE_TABLE = "s2j_write_it"


@pytest.fixture
def write_table(database):
    """Provide a fresh, empty write table and drop it afterwards.

    Yields the same `database` dict the other tests use. The autocommit-by-default
    path is what persists the CREATE here, so the fixture also exercises it.
    """
    name, config = database["name"], database["config"]
    run_query2json(name, f"DROP TABLE IF EXISTS {_WRITE_TABLE}", config=config)
    run_query2json(name, f"CREATE TABLE {_WRITE_TABLE} (id INTEGER)", config=config)
    try:
        yield database
    finally:
        run_query2json(name, f"DROP TABLE IF EXISTS {_WRITE_TABLE}", config=config)


def _count(database):
    rows = run_query2json(
        database["name"],
        f"SELECT COUNT(*) AS n FROM {_WRITE_TABLE}",
        config=database["config"],
    )
    return rows[0]["n"]


def test_ddl_rowcount_is_zero(database):
    """DDL reports {"rowcount": 0} on every backend (drivers vary: -1 on PG, 0 on
    MySQL), so the clamp gives a consistent contract."""
    name, config = database["name"], database["config"]
    run_query2json(name, "DROP TABLE IF EXISTS s2j_ddl", config=config)
    try:
        result = run_query2json(
            name, "CREATE TABLE s2j_ddl (id INTEGER)", config=config
        )
        assert result == {"rowcount": 0}
    finally:
        run_query2json(name, "DROP TABLE IF EXISTS s2j_ddl", config=config)


def test_insert_commits_by_default(write_table):
    """A bare INSERT persists across a separate invocation and reports rowcount."""
    result = run_query2json(
        write_table["name"],
        f"INSERT INTO {_WRITE_TABLE} VALUES (1)",
        config=write_table["config"],
    )
    assert result == {"rowcount": 1}
    assert _count(write_table) == 1


def test_update_returns_affected_rowcount(write_table):
    """UPDATE reports the affected-row count and persists."""
    for i in (1, 2, 3):
        run_query2json(
            write_table["name"],
            f"INSERT INTO {_WRITE_TABLE} VALUES ({i})",
            config=write_table["config"],
        )
    result = run_query2json(
        write_table["name"],
        f"UPDATE {_WRITE_TABLE} SET id = id + 10 WHERE id > 1",
        config=write_table["config"],
    )
    assert result == {"rowcount": 2}


def test_read_only_insert_is_rejected_and_not_persisted(write_table):
    """`SET TRANSACTION READ ONLY` rejects the write; nothing persists."""
    result = run_query2json(
        write_table["name"],
        f"INSERT INTO {_WRITE_TABLE} VALUES (99)",
        read_only=True,
        config=write_table["config"],
    )
    # The DB rejects the write, reported as a soft rowcount dict (not an error).
    assert isinstance(result, dict) and "rowcount" in result
    assert _count(write_table) == 0


def test_read_only_select_returns_rows(write_table):
    """SELECT under --read-only behaves like a normal read."""
    run_query2json(
        write_table["name"],
        f"INSERT INTO {_WRITE_TABLE} VALUES (1)",
        config=write_table["config"],
    )
    rows = run_query2json(
        write_table["name"],
        f"SELECT id FROM {_WRITE_TABLE}",
        read_only=True,
        config=write_table["config"],
    )
    assert rows == [{"id": 1}]


def test_cli_read_only_write_warns_on_stderr(write_table):
    """End-to-end CLI: a write under --read-only prints the stderr notice."""
    result = run_cli(
        "--read-only",
        "--name",
        write_table["name"],
        "--query",
        f"INSERT INTO {_WRITE_TABLE} VALUES (5)",
        "--config",
        write_table["config"],
    )
    assert result.returncode == 0, result.stderr
    assert "read-only mode: write not persisted" in result.stderr
    json.loads(result.stdout)  # stdout stays clean JSON
    assert _count(write_table) == 0
