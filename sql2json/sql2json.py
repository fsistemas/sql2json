import datetime
import json
import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.sql import text

from .parameter import parse_parameter


def map_result_proxy2list_dict(result_proxy) -> list:
    keys = list(result_proxy.keys())
    return [dict(zip(keys, row)) for row in result_proxy]


def run_query(engine, raw_query: str, **kwargs) -> list:
    current_date = datetime.date.today()
    parameters = {k: parse_parameter(v, current_date) for k, v in kwargs.items()}

    with engine.connect() as con:
        result_proxy = con.execute(text(raw_query), parameters)
        records = map_result_proxy2list_dict(result_proxy)

    return records


def load_config_file(config_path: str) -> dict:
    try:
        with open(config_path) as json_file:
            return json.load(json_file)
    except Exception:
        pass

    return {
        "conections": {"default": "sqlite:///test.db"},
        "queries": {"default": "SELECT 1 AS a, 2 AS b"},
    }


def _find_config() -> str:
    """
    Return the first config file found using this lookup order:
      1. ./sql2json.json
      2. ./.sql2json/config.json
      3. ~/.sql2json/config.json  (may not exist — load_config_file falls back to
                                   an in-memory test DB when the file is missing)
    """
    candidates = [
        os.path.join(os.getcwd(), "sql2json.json"),
        os.path.join(os.getcwd(), ".sql2json", "config.json"),
        os.path.join(os.path.expanduser("~"), ".sql2json", "config.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[-1]


def load_query_from_file(sql_file_path: str) -> str:
    file_name = sql_file_path

    if sql_file_path.startswith("@"):
        file_name = sql_file_path[1:]

    with open(file_name, "r") as file:
        return file.read()


def get_for_key_or_first_map_value(my_dict: dict, key: Optional[str] = None):
    if key in my_dict:
        return my_dict.get(key)

    for _, v in my_dict.items():
        return v

    return ""


def list_connections(config_path: Optional[str] = None) -> list:
    """Return the names of all configured database connections."""
    path = config_path or _find_config()
    config = load_config_file(path)
    return list(config.get("conections", {}).keys())


def list_queries(config_path: Optional[str] = None) -> list:
    """Return the names of all configured queries."""
    path = config_path or _find_config()
    config = load_config_file(path)
    return list(config.get("queries", {}).keys())


def run_query_by_name(
    conection_name: str = "default", query_name: str = "default", **kwargs
) -> list:
    """
    Run a SQL query given a conection_name, query_name.
    Returns a list of dicts.
    """
    # Pop config before passing kwargs to SQLAlchemy so it isn't treated as a bind param
    config_path = kwargs.pop("config", None) or _find_config()

    config = load_config_file(config_path)

    config_dbs = config.get("conections", {})
    config_queries = config.get("queries", {})

    # If conection_name does not exist, try to use as connection string
    conection_string = config_dbs.get(conection_name, conection_name)

    # If query_name does not exist, try to use as inline SQL
    raw_query_string = config_queries.get(query_name, query_name)

    if raw_query_string.startswith("@"):
        raw_query_string = load_query_from_file(raw_query_string[1:])

    engine = create_engine(conection_string)

    return run_query(engine, raw_query_string, **kwargs)


def parse_json_columns(result: dict, jsonkeys: str = "") -> dict:
    """
    Convert string-encoded JSON columns to parsed objects.
    jsonkeys: comma-separated column names whose values should be parsed as JSON.
    """
    jsonkeys_list = []

    if type(jsonkeys) is tuple:
        jsonkeys_list = [key.strip() for key in jsonkeys]
    elif type(jsonkeys) is str:
        jsonkeys_list = [key.strip() for key in jsonkeys.split(",")]

    if not jsonkeys_list:
        return result

    response = {}

    for key in result:
        if key in jsonkeys_list:
            response[key] = json.loads(result[key])
        else:
            response[key] = result[key]

    return response


def run_query2json(
    name: str = "default",
    query: str = "default",
    wrapper: bool = False,
    first: bool = False,
    key: str = "",
    value: str = "",
    jsonkeys: str = "",
    **kwargs,
):
    """
    Run a SQL query and return results with optional transformations.

    name: Connection name in config file or a SQLAlchemy connection string.
    query: Query name in config file, raw SQL, or @/path/to/file.sql.
    wrapper: Wrap result list in {"data": [...]}.
    first: Return only the first row.
    key: Column name to use as key (with value) or extract as scalar (with first).
    value: Column name to use as value (used with key).
    jsonkeys: Comma-separated columns whose string values should be parsed as JSON.
    """
    unparsed_results = run_query_by_name(name, query, **kwargs)

    results = [parse_json_columns(result, jsonkeys) for result in unparsed_results]

    result = None

    if first:
        if results and len(results) > 0:
            item = results[0]

            if key and value:
                result = {item.get(key): item.get(value)}
            else:
                result = get_for_key_or_first_map_value(item, key) if key else item
        else:
            result = "" if key and not value else {}
    else:
        if key and value:
            result = [
                {item.get(key): item.get(value)}
                if key and key in item and value in item
                else item
                for item in results
            ]
        else:
            result = [
                item.get(key) if key and key in item else item for item in results
            ]

    if wrapper:
        return {"data": result}
    else:
        return result
