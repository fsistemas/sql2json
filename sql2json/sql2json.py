import datetime
import json
import os

from sqlalchemy import create_engine
from sqlalchemy.sql import text

from .parameter import parse_parameter


def map_result_proxy2list_dict(result_proxy):
    """
    Map a sqlalchemy result_proxy to a list of dict
    """
    return [dict(zip(row.keys(), row)) for row in result_proxy]


def run_query(engine, raw_query, **kwargs):
    """
    Run query convert to list of dict
    """

    current_date = datetime.date.today()

    # Parse/format parameters before use
    parameters = {k: parse_parameter(v, current_date) for k, v in kwargs.items()}

    with engine.connect() as con:
        result_proxy = con.execute(text(raw_query), parameters)

        records = map_result_proxy2list_dict(result_proxy)

    return records


def load_config_file(config_path):
    """ Load config file from config_path or test configuration """

    try:
        with open(config_path) as json_file:
            return json.load(json_file)
    except Exception:
        pass

    return {
        "conections": {"default": "sqlite:///test.db"},
        "queries": {"default": "SELECT 1 AS a, 2 AS b"},
    }


def load_query_from_file(sql_file_path):
    """
    Read file and return content as string
    """

    file_name = sql_file_path

    if sql_file_path.startswith("@"):
        file_name = sql_file_path[1:]

    with open(file_name, "r") as file:
        return file.read()


def get_for_key_or_first_map_value(my_dict, key=None):
    """
    Return the value in key "key" or the first value from a map
    """

    if key in my_dict:
        return my_dict.get(key)

    for _, v in my_dict.items():
        return v

    return ""


def run_query_by_name(conection_name="default", query_name="default", **kwargs):
    """
    Run a SQL query given a conection_name, query_name
    Return a list o dicts
    """
    user_home = os.environ["HOME"]
    user_home_config_path = user_home + "/.sql2json/config.json"

    config_path = kwargs.get("config", user_home_config_path)

    config = load_config_file(config_path)

    config_dbs = config.get("conections", {})
    config_queries = config.get("queries", {})

    # If conection_name does not exists, try to use as conection string
    conection_string = config_dbs.get(conection_name, conection_name)

    # If query_name does not exists, try to use as online query
    raw_query_string = config_queries.get(query_name, query_name)

    if raw_query_string.startswith("@"):
        # Load query from file
        raw_query_string = load_query_from_file(raw_query_string[1:])

    engine = create_engine(conection_string)

    return run_query(engine, raw_query_string, **kwargs)


def parse_json_columns(result, jsonkeys=""):
    """
    result: dict, row from database
    jsonkeys: Comma separated json columns in result
    Convert to json columns listed in jsonkeys
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
    name="default",
    query="default",
    wrapper=False,
    first=False,
    key="",
    value="",
    jsonkeys="",
    **kwargs
):
    """
    Run a SQL query given a conection_name, query_name
    Depending on parameters transform results
    name: Conection name in config file or a sqlalchemy conection string
    query: Query  name in config file or raw sql query
    wrapper: When you can't acept an array this help to wrap result on a object with atribute data
    first: For return the first element only
    key: column name to usa as key with value. If you use only key then return value
    value: column name to use as value. Useful only with key
    jsonkeys: Coma separated columns what are json object/array in database
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
        wrappered_result = {"data": result}

        return wrappered_result
    else:
        return result
