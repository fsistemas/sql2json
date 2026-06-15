from sql2json import run_query2json

rows = run_query2json(
    name="sqlite:///:memory:",
    query="SELECT json_object('name', 'Ada', 'active', 1) AS payload",
    jsonkeys="payload",
)

print(rows)
