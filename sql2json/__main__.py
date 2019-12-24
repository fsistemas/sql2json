from __future__ import print_function

import fire
import json

from .sql2json import run_query_by_name

def get_first_map_value(my_dict):
    for _, v in my_dict.items():
        return v

    return ""

def handle_run_query2json(name='default', query='default', wrapper=False, first = False, value=False):
    results = run_query_by_name(name, query)

    result = None

    is_empty = False

    if(first):
        if results and len(results) > 0:
            result = get_first_map_value(results[0]) if value else results[0]
        else:
            result = "" if value else {}
            is_empty = True
    else:
        result = results
        is_empty = True if not results else False

    if wrapper:
        wrappered_result = {
            'empty': is_empty,
            'data': result
        }

        print(json.dumps(wrappered_result))
    else:
        if value and first:
            print(result)
        else:
            print(json.dumps(result))

if __name__ == "__main__":
    fire.Fire(handle_run_query2json)
