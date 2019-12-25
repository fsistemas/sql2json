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

def run_query(engine, raw_query, **kwargs):
    """
    Run query convert to list of dict
    """

    with engine.connect() as con:
        result_proxy = con.execute(raw_query, kwargs)

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

    return run_query(engine, raw_query_string, **kwargs)

def run_query2json(name='default', query='default', wrapper=False, first = False, key='', **kwargs):
    """
    Run a SQL query given a conection_name, query_name
    Depending on parameters transform results
    name: Conection name in config file or a sqlalchemy conection string
    query: Query  name in config file or raw sql query
    wrapper: When you can't acept an array this help to wrap result on a object with atribute data
    first: For return the first element only
    key: column name to get or first column on results, useful only with first
    """

    results = run_query_by_name(name, query, **kwargs)

    result = None

    is_empty = False

    if(first):
        if results and len(results) > 0:
            result = get_for_key_or_first_map_value(results[0], key) if key else results[0]
        else:
            result = "" if key else {}
            is_empty = True
    else:
        result = results
        is_empty = True if not results else False

    if wrapper:
        wrappered_result = {
            'empty': is_empty,
            'data': result
        }

        return wrappered_result
    else:
        return result
