import json
import tempfile
from pathlib import Path

from sql2json import list_connections, list_queries

config = {
    "connections": {"default": "sqlite:///:memory:", "reporting": "sqlite:///:memory:"},
    "queries": {"default": "SELECT 1 AS ok", "sales": "SELECT 42 AS total"},
    "connection_queries": {
        "default": {"sales": "SELECT 7 AS scoped_sales"},
        "reporting": {"pipeline": "SELECT 8 AS pipeline"},
    },
}

with tempfile.TemporaryDirectory() as tmp:
    config_path = Path(tmp) / "sql2json.json"
    config_path.write_text(json.dumps(config))

    print(list_connections(str(config_path)))
    print(list_queries(str(config_path)))
    print(list_queries(str(config_path), scoped=True))
    print(list_queries(str(config_path), connection="default"))
