from __future__ import print_function

import csv
import json
import sys
from decimal import Decimal

import fire

from .parameter import parse_parameter
from .sql2json import (
    _current_date,
    list_connections as _list_connections,
    list_queries as _list_queries,
    run_query2json,
)


def _parse_filename_after_brackets(part, current_date):
    if "}" in part:
        new_parts = [parse_parameter(item, current_date) for item in part.split("}")]
        return "".join(new_parts)
    return parse_parameter(part, current_date)


def parse_filename(file_name, current_date):
    parts = file_name.split("{")
    results = [_parse_filename_after_brackets(part, current_date) for part in parts]
    return "".join(results)


def json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def json_dumps(value):
    return json.dumps(value, default=json_default)


def save_json(rows, file_name, timezone=None):
    current_date = _current_date(timezone)
    parsed_filename = parse_filename(file_name, current_date)

    final_file_name = (
        parsed_filename if ".json" in parsed_filename else parsed_filename + ".json"
    )

    with open(final_file_name, "w") as outfile:
        outfile.write(json_dumps(rows))


def save_csv(rows, file_name, dialect, key, timezone=None):
    current_date = _current_date(timezone)
    parsed_filename = parse_filename(file_name, current_date)

    ext = ".xls" if dialect == "excel" else ".csv"

    final_file_name = (
        parsed_filename if ext in parsed_filename else parsed_filename + ext
    )

    first_row = None
    final_rows = None

    try:
        if isinstance(rows, str):
            first_row = {}
            final_key = key if key else "key"
            first_row[final_key] = rows
            final_rows = [first_row]
        elif isinstance(rows, dict):
            first_row = rows
            final_rows = [rows]
        else:
            first_row = rows[0]
            final_rows = rows
    except Exception:
        pass

    csv_columns = first_row.keys()

    with open(final_file_name, "w") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=csv_columns,
            dialect=dialect if dialect == "excel" else None,
        )
        writer.writeheader()

        for data in final_rows:
            writer.writerow(data)


def handle_run_query2json(
    name="default",
    query="default",
    wrapper=False,
    first=False,
    key="",
    value="",
    jsonkeys="",
    format="json",
    output=None,
    list_connections=False,
    list_queries=False,
    timezone=None,
    **kwargs
):
    try:
        if list_connections:
            config_path = kwargs.get("config")
            print(json.dumps(_list_connections(config_path)))
            return

        if list_queries:
            config_path = kwargs.get("config")
            print(json.dumps(_list_queries(config_path)))
            return

        result = run_query2json(name, query, wrapper, first, key, value, jsonkeys, timezone=timezone, **kwargs)

        if output:
            if "csv" == format:
                save_csv(result, output, "csv", key, timezone=timezone)
            elif "excel" == format:
                save_csv(result, output, "excel", key, timezone=timezone)
            else:
                save_json(result, output, timezone=timezone)
        else:
            if key and value and first:
                print(json_dumps(result))
            elif key and first:
                print(result)
            else:
                print(json_dumps(result))

    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    fire.Fire(handle_run_query2json)
