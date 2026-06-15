from sql2json import run_query2json

rows = run_query2json(
    name="sqlite:///:memory:",
    query="SELECT :start_date AS start_date, :end_date AS end_date",
    timezone="UTC",
    start_date="START_CURRENT_MONTH|%Y-%m-%d 00:00:00",
    end_date="END_CURRENT_MONTH|%Y-%m-%d 23:59:59",
)

print(rows)
