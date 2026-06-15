from sqlalchemy.exc import SQLAlchemyError

from sql2json import run_query2json

try:
    run_query2json(
        name="sqlite:///:memory:",
        query="SELECT * FROM missing_table",
    )
except SQLAlchemyError as exc:
    print(type(exc).__name__)
