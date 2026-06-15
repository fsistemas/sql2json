from sql2json import run_query2json

rows = run_query2json(
    name="sqlite:///:memory:",
    query="SELECT 1 AS id, 'Ada' AS name",
)

print(rows)
