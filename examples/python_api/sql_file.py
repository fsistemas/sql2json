import tempfile
from pathlib import Path

from sql2json import run_query2json

with tempfile.TemporaryDirectory() as tmp:
    sql_path = Path(tmp) / "query.sql"
    sql_path.write_text("SELECT :answer AS answer")

    rows = run_query2json(
        name="sqlite:///:memory:",
        query=f"@{sql_path}",
        answer=123,
    )

print(rows)
