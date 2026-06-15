"""
Tests for the CLI output/serialization helpers in sql2json.__main__ and the
end-to-end --output file-writing path.

Unit tests exercise the helpers directly with temp files; the CLI tests run
sql2json as a subprocess. Nothing is written to the repo root.
"""

import csv
import datetime
import json
import os
import subprocess
import sys
from decimal import Decimal

import pytest

from sql2json.__main__ import (
    handle_run_query2json,
    json_default,
    json_dumps,
    parse_filename,
    save_csv,
    save_json,
)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIXED_DATE = datetime.date(2019, 12, 30)


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


class TestParseFilename:
    def test_plain_name_unchanged(self):
        assert parse_filename("report.json", FIXED_DATE) == "report.json"

    def test_current_date_placeholder_is_resolved(self):
        assert (
            parse_filename("report_{CURRENT_DATE}.json", FIXED_DATE)
            == "report_2019-12-30.json"
        )

    def test_multiple_placeholders(self):
        assert (
            parse_filename("{CURRENT_DATE}_to_{CURRENT_DATE}.csv", FIXED_DATE)
            == "2019-12-30_to_2019-12-30.csv"
        )


class TestJsonDefault:
    def test_decimal_becomes_float(self):
        assert json_default(Decimal("5000.00")) == 5000.0

    def test_unsupported_type_raises_typeerror(self):
        with pytest.raises(TypeError):
            json_default({1, 2, 3})

    def test_json_dumps_serializes_decimal_rows(self):
        assert json_dumps([{"amount": Decimal("1.50")}]) == '[{"amount": 1.5}]'


class TestSaveJson:
    def test_appends_json_extension(self, tmp_path):
        target = tmp_path / "report"
        save_json([{"a": 1}], str(target))
        written = tmp_path / "report.json"
        assert written.exists()
        assert json.loads(written.read_text()) == [{"a": 1}]

    def test_keeps_existing_json_extension(self, tmp_path):
        target = tmp_path / "report.json"
        save_json([{"a": 1}], str(target))
        assert target.exists()
        assert not (tmp_path / "report.json.json").exists()

    def test_serializes_decimal(self, tmp_path):
        target = tmp_path / "money.json"
        save_json([{"amount": Decimal("9.99")}], str(target))
        assert json.loads(target.read_text()) == [{"amount": 9.99}]


class TestSaveCsv:
    def test_list_of_dicts_writes_header_and_rows(self, tmp_path):
        target = tmp_path / "out"
        save_csv([{"a": 1, "b": 2}, {"a": 3, "b": 4}], str(target), "csv", "")
        written = tmp_path / "out.csv"
        assert written.exists()
        rows = list(csv.DictReader(written.open()))
        assert rows == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]

    def test_scalar_string_uses_default_key(self, tmp_path):
        target = tmp_path / "scalar"
        save_csv("hello", str(target), "csv", "")
        rows = list(csv.DictReader((tmp_path / "scalar.csv").open()))
        assert rows == [{"key": "hello"}]

    def test_scalar_string_uses_provided_key(self, tmp_path):
        target = tmp_path / "scalar"
        save_csv("hello", str(target), "csv", "label")
        rows = list(csv.DictReader((tmp_path / "scalar.csv").open()))
        assert rows == [{"label": "hello"}]

    def test_single_dict_writes_one_row(self, tmp_path):
        target = tmp_path / "single"
        save_csv({"a": 1, "b": 2}, str(target), "csv", "")
        rows = list(csv.DictReader((tmp_path / "single.csv").open()))
        assert rows == [{"a": "1", "b": "2"}]

    def test_excel_dialect_uses_xls_extension(self, tmp_path):
        target = tmp_path / "book"
        save_csv([{"a": 1}], str(target), "excel", "")
        assert (tmp_path / "book.xls").exists()

    def test_empty_rows_raises(self, tmp_path):
        # Degenerate input: an empty result set has no columns to write.
        target = tmp_path / "empty"
        with pytest.raises(Exception):
            save_csv([], str(target), "csv", "")


class TestCliOutput:
    def test_json_output_creates_file(self, tmp_path):
        target = tmp_path / "result"
        result = run_cli(
            "--name",
            "sqlite:///:memory:",
            "--query",
            "SELECT 1 AS a, 2 AS b",
            "--output",
            str(target),
        )
        assert result.returncode == 0
        written = tmp_path / "result.json"
        assert written.exists()
        assert json.loads(written.read_text()) == [{"a": 1, "b": 2}]

    def test_json_output_keeps_stdout_empty(self, tmp_path):
        target = tmp_path / "result"
        result = run_cli(
            "--name",
            "sqlite:///:memory:",
            "--query",
            "SELECT 1 AS a",
            "--output",
            str(target),
        )
        assert result.stdout == ""

    def test_csv_output_creates_csv_file(self, tmp_path):
        target = tmp_path / "result"
        result = run_cli(
            "--name",
            "sqlite:///:memory:",
            "--query",
            "SELECT 1 AS a, 2 AS b",
            "--format",
            "csv",
            "--output",
            str(target),
        )
        assert result.returncode == 0
        written = tmp_path / "result.csv"
        assert written.exists()
        rows = list(csv.DictReader(written.open()))
        assert rows == [{"a": "1", "b": "2"}]

    @pytest.mark.xfail(
        reason="FRA-172: --format csv also writes a stray .json file",
        strict=True,
    )
    def test_csv_output_does_not_create_json(self, tmp_path):
        target = tmp_path / "result"
        run_cli(
            "--name",
            "sqlite:///:memory:",
            "--query",
            "SELECT 1 AS a, 2 AS b",
            "--format",
            "csv",
            "--output",
            str(target),
        )
        # Desired behavior: csv output should not also produce a .json file.
        # Currently fails (xfail) until FRA-172 is fixed; will xpass after.
        assert not (tmp_path / "result.json").exists()

    def test_excel_output_creates_xls_file(self, tmp_path):
        target = tmp_path / "result"
        result = run_cli(
            "--name",
            "sqlite:///:memory:",
            "--query",
            "SELECT 1 AS a, 2 AS b",
            "--format",
            "excel",
            "--output",
            str(target),
        )
        assert result.returncode == 0
        assert (tmp_path / "result.xls").exists()

    def test_output_filename_resolves_date_placeholder(self, tmp_path):
        target = tmp_path / "report_{CURRENT_DATE}"
        result = run_cli(
            "--name",
            "sqlite:///:memory:",
            "--query",
            "SELECT 1 AS a",
            "--output",
            str(target),
            "--timezone",
            "UTC",
        )
        assert result.returncode == 0
        produced = list(tmp_path.glob("report_*.json"))
        assert len(produced) == 1


CONFIG = {
    "conections": {"default": "sqlite:///:memory:", "reporting": "sqlite:///:memory:"},
    "queries": {"default": "SELECT 1 AS a, 2 AS b", "sales": "SELECT 42 AS total"},
}


def _write_config(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(CONFIG))
    return str(cfg)


class TestHandleRunQuery2Json:
    """In-process tests for the CLI entry point so its branches are covered."""

    def test_prints_json_to_stdout(self, capsys, tmp_path):
        handle_run_query2json(query="SELECT 7 AS n", config=_write_config(tmp_path))
        out = json.loads(capsys.readouterr().out)
        assert out == [{"n": 7}]

    def test_list_connections_branch(self, capsys, tmp_path):
        handle_run_query2json(list_connections=True, config=_write_config(tmp_path))
        names = json.loads(capsys.readouterr().out)
        assert sorted(names) == ["default", "reporting"]

    def test_list_queries_branch(self, capsys, tmp_path):
        handle_run_query2json(list_queries=True, config=_write_config(tmp_path))
        names = json.loads(capsys.readouterr().out)
        assert sorted(names) == ["default", "sales"]

    def test_key_first_prints_scalar(self, capsys, tmp_path):
        handle_run_query2json(
            query="SELECT 42 AS total",
            key="total",
            first=True,
            config=_write_config(tmp_path),
        )
        assert capsys.readouterr().out.strip() == "42"

    def test_key_value_first_prints_json_pair(self, capsys, tmp_path):
        handle_run_query2json(
            query="SELECT 'a' AS k, 1 AS v",
            key="k",
            value="v",
            first=True,
            config=_write_config(tmp_path),
        )
        assert json.loads(capsys.readouterr().out) == {"a": 1}

    def test_json_output_to_file(self, tmp_path):
        target = tmp_path / "result"
        handle_run_query2json(
            query="SELECT 1 AS a",
            output=str(target),
            config=_write_config(tmp_path),
        )
        assert json.loads((tmp_path / "result.json").read_text()) == [{"a": 1}]

    def test_csv_output_to_file(self, tmp_path):
        target = tmp_path / "result"
        handle_run_query2json(
            query="SELECT 1 AS a, 2 AS b",
            format="csv",
            output=str(target),
            config=_write_config(tmp_path),
        )
        rows = list(csv.DictReader((tmp_path / "result.csv").open()))
        assert rows == [{"a": "1", "b": "2"}]

    def test_excel_output_to_file(self, tmp_path):
        target = tmp_path / "book"
        handle_run_query2json(
            query="SELECT 1 AS a",
            format="excel",
            output=str(target),
            config=_write_config(tmp_path),
        )
        assert (tmp_path / "book.xls").exists()

    def test_error_path_exits_and_writes_json_stderr(self, capsys, tmp_path):
        with pytest.raises(SystemExit) as exc:
            handle_run_query2json(
                query="SELECT * FROM nonexistent_table",
                config=_write_config(tmp_path),
            )
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        error = json.loads(captured.err)
        assert "error" in error and "type" in error
