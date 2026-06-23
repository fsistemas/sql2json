import datetime
import json
from importlib.metadata import version

import pytest
import sql2json

from sql2json import __version__, run_query_by_name
from sql2json.sql2json import _current_date


def test_version_matches_package_metadata():
    assert __version__ == version("sql2json")


def test_top_level_public_surface():
    assert sql2json.__all__ == [
        "__version__",
        "parse_parameter",
        "list_connections",
        "list_queries",
        "run_query_by_name",
        "run_query2json",
    ]


def test_run_query_by_name_empty_param():
    json_results = run_query_by_name()
    json_result = json_results[0]

    assert 1 == json_result["a"]
    assert 2 == json_result["b"]


def test_run_query_by_name_default_defalt_name():
    json_results = run_query_by_name("default")
    json_result = json_results[0]

    assert 1 == json_result["a"]
    assert 2 == json_result["b"]


def test_run_query_by_name_default_defalt_query():
    json_results = run_query_by_name(query_name="default")
    json_result = json_results[0]

    assert 1 == json_result["a"]
    assert 2 == json_result["b"]


def test_run_query_by_name_default():
    json_results = run_query_by_name("default", "default")
    json_result = json_results[0]

    assert 1 == json_result["a"]
    assert 2 == json_result["b"]


def test_run_query_raw_sql():
    json_results = run_query_by_name("default", "SELECT 11 AS a, 22 AS b")
    json_result = json_results[0]

    assert 11 == json_result["a"]
    assert 22 == json_result["b"]


class TestCurrentDate:
    def test_no_timezone_returns_date(self):
        assert isinstance(_current_date(), datetime.date)

    def test_utc_returns_date(self):
        assert isinstance(_current_date("UTC"), datetime.date)

    def test_named_timezone_returns_date(self):
        assert isinstance(_current_date("America/New_York"), datetime.date)

    def test_invalid_timezone_raises(self):
        with pytest.raises(Exception):
            _current_date("Invalid/Zone")


def test_run_query_raw_sql_parameters():
    x = 10
    y = 20

    query = "SELECT :x AS a, :y AS b, :x + :y AS xy"

    json_results = run_query_by_name("default", query, x=x, y=y)
    json_result = json_results[0]

    assert x == json_result["a"]
    assert y == json_result["b"]
    assert x + y == json_result["xy"]


def _write_config(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


def test_run_query_by_name_uses_connection_scoped_query(tmp_path):
    cfg = tmp_path / "config.json"
    _write_config(
        cfg,
        {
            "connections": {"default": "sqlite:///:memory:"},
            "connection_queries": {"default": {"answer": "SELECT 246 AS ticket"}},
            "queries": {},
        },
    )

    json_results = run_query_by_name("default", "answer", config=str(cfg))

    assert json_results == [{"ticket": 246}]


def test_run_query_by_name_falls_back_to_global_query(tmp_path):
    cfg = tmp_path / "config.json"
    _write_config(
        cfg,
        {
            "connections": {"default": "sqlite:///:memory:"},
            "connection_queries": {"default": {"scoped": "SELECT 1 AS scoped"}},
            "queries": {"global": "SELECT 2 AS global_value"},
        },
    )

    json_results = run_query_by_name("default", "global", config=str(cfg))

    assert json_results == [{"global_value": 2}]


def test_run_query_by_name_scoped_query_takes_precedence_over_global(tmp_path):
    cfg = tmp_path / "config.json"
    _write_config(
        cfg,
        {
            "connections": {"default": "sqlite:///:memory:"},
            "connection_queries": {"default": {"same": "SELECT 'scoped' AS source"}},
            "queries": {"same": "SELECT 'global' AS source"},
        },
    )

    json_results = run_query_by_name("default", "same", config=str(cfg))

    assert json_results == [{"source": "scoped"}]


def test_run_query_by_name_rejects_malformed_connection_queries(tmp_path):
    cfg = tmp_path / "config.json"
    _write_config(
        cfg,
        {
            "connections": {"default": "sqlite:///:memory:"},
            "connection_queries": {"default": "SELECT 1"},
            "queries": {},
        },
    )

    with pytest.raises(
        ValueError, match="connection_queries.default must be an object"
    ):
        run_query_by_name("default", "anything", config=str(cfg))


def test_run_query_by_name_rejects_connection_queries_for_unknown_connection(tmp_path):
    cfg = tmp_path / "config.json"
    _write_config(
        cfg,
        {
            "connections": {"default": "sqlite:///:memory:"},
            "connection_queries": {"missing": {"answer": "SELECT 1"}},
            "queries": {},
        },
    )

    with pytest.raises(
        ValueError, match="connection_queries references unknown connection 'missing'"
    ):
        run_query_by_name("default", "anything", config=str(cfg))
