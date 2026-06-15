import json
import tempfile
from pathlib import Path

from sql2json import list_connections, list_queries

config = {
    "connections": {"default": "sqlite:///:memory:", "reporting": "sqlite:///:memory:"},
    "queries": {"default": "SELECT 1 AS ok", "sales": "SELECT 42 AS total"},
}

with tempfile.TemporaryDirectory() as tmp:
    config_path = Path(tmp) / "sql2json.json"
    config_path.write_text(json.dumps(config))

    print(list_connections(str(config_path)))
    print(list_queries(str(config_path)))
