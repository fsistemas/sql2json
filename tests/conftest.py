import pytest


@pytest.fixture(autouse=True)
def _isolate_home(tmp_path, monkeypatch):
    """Keep tests independent of ~/.sql2json/config.json on the developer's machine.

    _find_config() searches HOME last. Without this fixture it finds the real user
    config, causing tests that rely on the built-in SQLite fallback to fail or
    produce machine-specific results.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
