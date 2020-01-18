from __future__ import print_function

import json

import fire

from .sql2json import run_query2json


def handle_run_query2json(
    name="default",
    query="default",
    wrapper=False,
    first=False,
    key="",
    value="",
    jsonkeys="",
    **kwargs
):
    result = run_query2json(name, query, wrapper, first, key, value, jsonkeys, **kwargs)

    if key and value and first:
        print(json.dumps(result))
    elif key and first:
        print(result)
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    fire.Fire(handle_run_query2json)
