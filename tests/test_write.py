"""
Unit tests for the write path (autocommit by default) and the ``--read-only``
safe mode.

These run in-process. Persistence is verified against a *file-based* SQLite
database in tmp_path (a ``sqlite:///:memory:`` URL would give each new engine its
own empty database, so it cannot show that a commit survived across calls).
"""

import json

import pytest

from sql2json import run_query2json, run_query_by_name
from sql2json.sql2json import _coerce_bool


def _file_db_config(tmp_path):
    """Write a config mapping the `db` connection to a file-backed SQLite DB."""
    db = tmp_path / "test.db"
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps(
            {
                "connections": {"db": f"sqlite:///{db}"},
                "queries": {},
            }
        )
    )
    return str(cfg)


class TestAutocommitPersistence:
    def test_create_table_returns_rowcount(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        result = run_query2json("db", "CREATE TABLE t (id INTEGER)", config=cfg)
        # DDL rowcount is clamped to 0 for a consistent cross-database contract
        # (drivers report -1 on SQLite/PostgreSQL, 0 on MySQL).
        assert result == {"rowcount": 0}

    def test_insert_persists_and_returns_rowcount(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        run_query2json("db", "CREATE TABLE t (id INTEGER, name TEXT)", config=cfg)
        result = run_query2json(
            "db", "INSERT INTO t (id, name) VALUES (1, 'a')", config=cfg
        )
        assert result == {"rowcount": 1}

        rows = run_query2json("db", "SELECT COUNT(*) AS n FROM t", config=cfg)
        assert rows == [{"n": 1}]

    def test_update_returns_affected_rowcount(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        run_query2json("db", "CREATE TABLE t (id INTEGER, name TEXT)", config=cfg)
        run_query2json("db", "INSERT INTO t VALUES (1, 'a')", config=cfg)
        run_query2json("db", "INSERT INTO t VALUES (2, 'a')", config=cfg)
        result = run_query2json(
            "db", "UPDATE t SET name = 'b' WHERE name = 'a'", config=cfg
        )
        assert result == {"rowcount": 2}

    def test_delete_returns_affected_rowcount(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        run_query2json("db", "CREATE TABLE t (id INTEGER)", config=cfg)
        run_query2json("db", "INSERT INTO t VALUES (1)", config=cfg)
        run_query2json("db", "INSERT INTO t VALUES (2)", config=cfg)
        result = run_query2json("db", "DELETE FROM t WHERE id = 1", config=cfg)
        assert result == {"rowcount": 1}

    def test_parameterized_insert_persists(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        run_query2json("db", "CREATE TABLE t (id INTEGER)", config=cfg)
        result = run_query2json(
            "db", "INSERT INTO t (id) VALUES (:id)", id=7, config=cfg
        )
        assert result == {"rowcount": 1}

        rows = run_query2json("db", "SELECT id FROM t", config=cfg)
        assert rows == [{"id": 7}]

    def test_insert_with_date_variable_persists(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        run_query2json("db", "CREATE TABLE t (d TEXT)", config=cfg)
        run_query2json(
            "db",
            "INSERT INTO t (d) VALUES (:d)",
            d="CURRENT_DATE|%Y-%m-%d",
            timezone="UTC",
            config=cfg,
        )
        rows = run_query2json("db", "SELECT d FROM t", config=cfg)
        # A real date string was bound, not the literal "CURRENT_DATE" token.
        assert rows[0]["d"] != "CURRENT_DATE"
        assert len(rows[0]["d"]) == 10

    def test_run_query_by_name_no_row_statement_persists(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        run_query_by_name("db", "CREATE TABLE t (id INTEGER)", config=cfg)
        result = run_query_by_name("db", "INSERT INTO t VALUES (1)", config=cfg)
        assert result == {"rowcount": 1}
        rows = run_query_by_name("db", "SELECT COUNT(*) AS n FROM t", config=cfg)
        assert rows == [{"n": 1}]


class TestSelectTransforms:
    def test_first_and_key_returns_scalar(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        result = run_query2json("db", "SELECT 5 AS n", first=True, key="n", config=cfg)
        assert result == 5

    def test_key_value_returns_dict_list(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        result = run_query2json(
            "db", "SELECT 1 AS id, 'a' AS name", key="id", value="name", config=cfg
        )
        assert result == [{1: "a"}]

    def test_wrapper_true_wraps_rows_under_data(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        result = run_query2json("db", "SELECT 1 AS a", wrapper=True, config=cfg)
        assert result == {"data": [{"a": 1}]}

    def test_wrapper_string_wraps_rows_under_named_key(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        result = run_query2json("db", "SELECT 1 AS a", wrapper="items", config=cfg)
        assert result == {"items": [{"a": 1}]}


class TestWrapperOnRowcount:
    def test_wrapper_true_wraps_rowcount_under_data(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        run_query2json("db", "CREATE TABLE t (id INTEGER)", config=cfg)
        result = run_query2json(
            "db", "INSERT INTO t VALUES (1)", wrapper=True, config=cfg
        )
        assert result == {"data": {"rowcount": 1}}

    def test_wrapper_string_wraps_rowcount_under_named_key(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        run_query2json("db", "CREATE TABLE t (id INTEGER)", config=cfg)
        result = run_query2json(
            "db", "INSERT INTO t VALUES (1)", wrapper="result", config=cfg
        )
        assert result == {"result": {"rowcount": 1}}


class TestReadOnly:
    def test_read_only_write_does_not_persist(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        run_query2json("db", "CREATE TABLE t (id INTEGER)", config=cfg)

        result = run_query2json(
            "db", "INSERT INTO t VALUES (1)", read_only=True, config=cfg
        )
        # On SQLite the DB rejects the write, so rowcount is 0; on other backends
        # the rollback backstop applies. Either way it is a rowcount dict and
        # nothing persists — assert robustly.
        assert isinstance(result, dict)
        assert "rowcount" in result

        rows = run_query2json("db", "SELECT COUNT(*) AS n FROM t", config=cfg)
        assert rows == [{"n": 0}]

    def test_read_only_select_returns_rows(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        result = run_query2json(
            "db", "SELECT 1 AS a, 2 AS b", read_only=True, config=cfg
        )
        assert result == [{"a": 1, "b": 2}]

    def test_read_only_write_warns_on_stderr(self, tmp_path, capsys):
        cfg = _file_db_config(tmp_path)
        run_query2json("db", "CREATE TABLE t (id INTEGER)", config=cfg)
        run_query2json("db", "INSERT INTO t VALUES (1)", read_only=True, config=cfg)

        captured = capsys.readouterr()
        assert "read-only mode: write not persisted" in captured.err
        assert captured.out == ""  # notice never touches stdout

    def test_read_only_select_does_not_warn(self, tmp_path, capsys):
        cfg = _file_db_config(tmp_path)
        run_query2json("db", "SELECT 1 AS a", read_only=True, config=cfg)
        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == ""

    def test_read_only_does_not_leak_across_calls(self, tmp_path):
        cfg = _file_db_config(tmp_path)
        run_query2json("db", "CREATE TABLE t (id INTEGER)", config=cfg)

        # A read-only write first (SQLite sets PRAGMA query_only on a pooled conn)...
        run_query2json("db", "INSERT INTO t VALUES (1)", read_only=True, config=cfg)

        # ...a subsequent normal write must still persist (proves no leak/reset works).
        run_query2json("db", "INSERT INTO t VALUES (2)", config=cfg)
        rows = run_query2json("db", "SELECT COUNT(*) AS n FROM t", config=cfg)
        assert rows == [{"n": 1}]


class TestCoerceBool:
    @pytest.mark.parametrize(
        "value",
        [True, "true", "t", "yes", "y", "1", "on", "YES"],
    )
    def test_truthy(self, value):
        assert _coerce_bool(value) is True

    @pytest.mark.parametrize(
        "value",
        [False, "", "false", "no", "n", "0", "off", None],
    )
    def test_falsy(self, value):
        assert _coerce_bool(value) is False
