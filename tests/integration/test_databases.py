"""Real-database integration tests for the documented demo paths.

Covers, for both PostgreSQL and MySQL: named connection lookup, named query
lookup, bind parameters, numeric/Decimal values, and end-to-end JSON
serialization through the CLI. Marked `integration` (deselected by default);
see tests/integration/conftest.py for provisioning and clean-skip behavior.
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
