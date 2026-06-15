import json
import tempfile
from pathlib import Path

from sql2json import run_query_by_name

config = {
    "connections": {"default": "sqlite:///:memory:"},
    "queries": {"answer": "SELECT :value AS value"},
}

with tempfile.TemporaryDirectory() as tmp:
    config_path = Path(tmp) / "sql2json.json"
    config_path.write_text(json.dumps(config))

    rows = run_query_by_name(
        conection_name="default",
        query_name="answer",
        config=str(config_path),
        value=42,
    )

print(rows)
