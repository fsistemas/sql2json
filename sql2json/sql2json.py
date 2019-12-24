import json
import os
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.sql import text

def map_result_proxy2list_dict(result_proxy):
    """
    Map a sqlalchemy result_proxy to a list of dict
    """
    return [dict(zip(row.keys(), row)) for row in result_proxy]

def run_query(engine, raw_query):
    """
    Run query convert to list of dict
    """

    with engine.connect() as con:
        result_proxy = con.execute(raw_query)

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
        "conections": {
            "default": "sqlite:///test.db"
        },
        "queries": {
            "default": "SELECT 1 AS a, 2 AS b"
        }
    }

def run_query_by_name(conection_name="default", query_name="default"):
    """
    Run a query given a conection_name, query_name
    """
    user_home = os.environ['HOME']

    config_path = user_home + "/.sql2json/config.json"

    config = load_config_file(config_path)

    config_dbs = config["conections"]
    config_queries = config["queries"]

    #If conection_name does not exists, try to use as conection string
    conection_string = config_dbs.get(conection_name, conection_name)

    #If query_name does not exists, try to use as online query
    raw_query_string = config_queries.get(query_name, query_name)

    engine = create_engine(conection_string)

    return run_query(engine, raw_query_string)

