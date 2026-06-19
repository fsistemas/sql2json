"""
CLI integration tests.

These tests run sql2json as a subprocess so they exercise the full CLI surface
including fire arg parsing, discovery flags, and JSON error output.
"""

import json
import os
import shutil
import subprocess
import sys
from decimal import Decimal

import pytest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cli(*args, extra_env=None):
    env = {**os.environ, "PYTHONPATH": PROJECT_DIR}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "sql2json"] + list(args),
        capture_output=True,
        text=True,
        env=env,
    )


def _write_config(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


CONFIG = {
    "conections": {"default": "sqlite:///:memory:", "reporting": "sqlite:///:memory:"},
    "queries": {"default": "SELECT 1 AS a, 2 AS b", "sales": "SELECT 42 AS total"},
}


class TestDefaultQuery:
    def test_happy_path_exit_zero(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--config", cfg)
        assert result.returncode == 0

    def test_happy_path_stdout_is_json(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--config", cfg)
        rows = json.loads(result.stdout)
        assert rows[0]["a"] == 1
        assert rows[0]["b"] == 2

    def test_inline_sql(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli(
            "--name", "default", "--query", "SELECT 99 AS val", "--config", cfg
        )
        assert result.returncode == 0
        rows = json.loads(result.stdout)
        assert rows[0]["val"] == 99

    def test_decimal_results_are_json_serializable(self):
        from sql2json.__main__ import json_dumps

        rows = [{"amount": Decimal("5000.00")}]

        assert json_dumps(rows) == '[{"amount": 5000.0}]'


class TestListConnections:
    def test_exit_zero(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--list-connections", "--config", cfg)
        assert result.returncode == 0

    def test_stdout_is_json_array(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--list-connections", "--config", cfg)
        names = json.loads(result.stdout)
        assert isinstance(names, list)
        assert "default" in names
        assert "reporting" in names

    def test_stderr_is_empty(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--list-connections", "--config", cfg)
        assert result.stderr == ""

    def test_underscore_form_also_works(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--list_connections", "--config", cfg)
        assert result.returncode == 0
        assert isinstance(json.loads(result.stdout), list)


class TestListQueries:
    def test_exit_zero(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--list-queries", "--config", cfg)
        assert result.returncode == 0

    def test_stdout_is_json_array(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--list-queries", "--config", cfg)
        names = json.loads(result.stdout)
        assert isinstance(names, list)
        assert "default" in names
        assert "sales" in names

    def test_stderr_is_empty(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--list-queries", "--config", cfg)
        assert result.stderr == ""


class TestErrorOutput:
    def test_bad_query_exits_nonzero(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli(
            "--name",
            "default",
            "--query",
            "SELECT * FROM nonexistent_table",
            "--config",
            cfg,
        )
        assert result.returncode != 0

    def test_bad_query_stderr_is_json(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli(
            "--name",
            "default",
            "--query",
            "SELECT * FROM nonexistent_table",
            "--config",
            cfg,
        )
        error = json.loads(result.stderr)
        assert "error" in error
        assert "type" in error

    def test_bad_query_stdout_is_empty(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli(
            "--name",
            "default",
            "--query",
            "SELECT * FROM nonexistent_table",
            "--config",
            cfg,
        )
        assert result.stdout == ""

    def test_bad_connection_exits_nonzero(self):
        result = run_cli(
            "--name", "postgresql://bad:bad@localhost/nodb", "--query", "SELECT 1"
        )
        assert result.returncode != 0

    def test_bad_connection_stderr_is_json(self):
        result = run_cli(
            "--name", "postgresql://bad:bad@localhost/nodb", "--query", "SELECT 1"
        )
        error = json.loads(result.stderr)
        assert "error" in error
        assert "type" in error

    def test_library_api_still_raises(self, tmp_path):
        """Python API must raise normally — error envelope is CLI-only."""
        from sql2json import run_query2json

        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        with pytest.raises(Exception):
            run_query2json("default", "SELECT * FROM nonexistent_table", config=cfg)


class TestTimezone:
    def test_utc_exits_zero(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--timezone", "UTC", "--config", cfg)
        assert result.returncode == 0

    def test_named_timezone_exits_zero(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--timezone", "America/New_York", "--config", cfg)
        assert result.returncode == 0

    def test_timezone_result_is_valid_json(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--timezone", "UTC", "--config", cfg)
        rows = json.loads(result.stdout)
        assert rows[0]["a"] == 1

    def test_invalid_timezone_exits_nonzero(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--timezone", "Invalid/Zone", "--config", cfg)
        assert result.returncode != 0

    def test_invalid_timezone_stderr_is_json(self, tmp_path):
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = run_cli("--timezone", "Invalid/Zone", "--config", cfg)
        error = json.loads(result.stderr)
        assert "error" in error


class TestEntryPoint:
    """The `sql2json` console_scripts entry point (pyproject [project.scripts])."""

    def test_main_dispatches_to_fire(self, monkeypatch):
        import sql2json.__main__ as cli

        called = {}
        monkeypatch.setattr(cli.fire, "Fire", lambda fn: called.setdefault("fn", fn))
        cli.main()
        assert called["fn"] is cli.handle_run_query2json

    def test_console_script_runs(self, tmp_path):
        if shutil.which("sql2json") is None:
            pytest.skip("sql2json console script not installed on PATH")
        cfg = str(tmp_path / "config.json")
        _write_config(cfg, CONFIG)
        result = subprocess.run(
            ["sql2json", "--config", cfg],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert json.loads(result.stdout)[0]["a"] == 1
