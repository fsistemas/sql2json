from sql2json import run_query2json

query = "SELECT 'January' AS month, 5000 AS sales UNION ALL SELECT 'February', 3000"

print(run_query2json(name="sqlite:///:memory:", query=query, first=True))
print(run_query2json(name="sqlite:///:memory:", query=query, first=True, key="sales"))
print(
    run_query2json(name="sqlite:///:memory:", query=query, key="month", value="sales")
)
print(run_query2json(name="sqlite:///:memory:", query=query, wrapper=True))
