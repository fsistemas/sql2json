import json
import os
import tempfile

import pytest

from sql2json import list_connections, list_queries
from sql2json.sql2json import _find_config, run_query_by_name


def _write_config(tmp_path, data):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(data))
    return str(config_file)


CONFIG = {
    "conections": {
        "default": "sqlite:///:memory:",
        "reporting": "sqlite:///:memory:",
    },
    "queries": {
        "default": "SELECT 1 AS a, 2 AS b",
        "sales": "SELECT 42 AS total",
    },
}


class TestListConnections:
    def test_returns_all_connection_names(self, tmp_path):
        path = _write_config(tmp_path, CONFIG)
        result = list_connections(config_path=path)
        assert sorted(result) == ["default", "reporting"]

    def test_returns_list(self, tmp_path):
        path = _write_config(tmp_path, CONFIG)
        assert isinstance(list_connections(config_path=path), list)

    def test_fallback_config_has_default(self):
        # When no config file exists the in-memory test config is used
        result = list_connections(config_path="/nonexistent/path.json")
        assert "default" in result

    def test_empty_connections(self, tmp_path):
        path = _write_config(tmp_path, {"conections": {}, "queries": {}})
        assert list_connections(config_path=path) == []


class TestListQueries:
    def test_returns_all_query_names(self, tmp_path):
        path = _write_config(tmp_path, CONFIG)
        result = list_queries(config_path=path)
        assert sorted(result) == ["default", "sales"]

    def test_returns_list(self, tmp_path):
        path = _write_config(tmp_path, CONFIG)
        assert isinstance(list_queries(config_path=path), list)

    def test_fallback_config_has_default(self):
        result = list_queries(config_path="/nonexistent/path.json")
        assert "default" in result

    def test_empty_queries(self, tmp_path):
        path = _write_config(tmp_path, {"conections": {}, "queries": {}})
        assert list_queries(config_path=path) == []


class TestFindConfig:
    def test_prefers_sql2json_json_in_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "sql2json.json"
        config_file.write_text("{}")
        assert _find_config() == str(config_file)

    def test_falls_back_to_dot_sql2json_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        dot_dir = tmp_path / ".sql2json"
        dot_dir.mkdir()
        config_file = dot_dir / "config.json"
        config_file.write_text("{}")
        assert _find_config() == str(config_file)

    def test_sql2json_json_wins_over_dot_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        dot_dir = tmp_path / ".sql2json"
        dot_dir.mkdir()
        (dot_dir / "config.json").write_text("{}")
        top = tmp_path / "sql2json.json"
        top.write_text("{}")
        assert _find_config() == str(top)

    def test_returns_home_path_when_nothing_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = _find_config()
        assert result.endswith(os.path.join(".sql2json", "config.json"))


class TestConfigKwargNotLeakedToSQL:
    """Regression: --config must not be forwarded as a SQL bind parameter."""

    def test_config_kwarg_does_not_reach_sql(self, tmp_path):
        config = {
            "conections": {"default": "sqlite:///:memory:"},
            "queries": {"default": "SELECT 1 AS a, 2 AS b"},
        }
        path = _write_config(tmp_path, config)
        # If 'config' were passed to SQLAlchemy it would raise OperationalError
        # (unknown bind param). This must complete without error.
        results = run_query_by_name("default", "SELECT 1 AS ok", config=path)
        assert results[0]["ok"] == 1
