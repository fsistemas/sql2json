from __future__ import print_function

import fire
import json

from .sql2json import run_query2json

def handle_run_query2json(name='default', query='default', wrapper=False, first = False, key=False, **kwargs):
    result = run_query2json(name, query, wrapper, first, key, **kwargs)

    if key and first:
        print(result)
    else:
        print(json.dumps(result))

if __name__ == "__main__":
    fire.Fire(handle_run_query2json)
