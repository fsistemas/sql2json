from __future__ import print_function

import csv
import datetime
import json

import fire

from .parameter import parse_parameter
from .sql2json import run_query2json


def _parse_filename_after_brackets(part, current_date):
    if "}" in part:
        new_parts = [parse_parameter(item, current_date) for item in part.split("}")]
        return "".join(new_parts)
    return parse_parameter(part, current_date)


def parse_filename(file_name, current_date):
    parts = file_name.split("{")

    results = [_parse_filename_after_brackets(part, current_date) for part in parts]

    return "".join(results)


def save_json(rows, file_name):
    current_date = datetime.date.today()
    parsed_filename = parse_filename(file_name, current_date)

    final_file_name = (
        parsed_filename if ".json" in parsed_filename else parsed_filename + ".json"
    )

    with open(final_file_name, "w") as outfile:
        json.dump(rows, outfile)


def save_csv(rows, file_name, dialect, key):
    current_date = datetime.date.today()
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
    **kwargs
):
    result = run_query2json(name, query, wrapper, first, key, value, jsonkeys, **kwargs)

    if output:
        if "csv" == format:
            save_csv(result, output, "csv", key)
        if "excel" == format:
            save_csv(result, output, "excel", key)
        else:
            save_json(result, output)
    else:
        if key and value and first:
            print(json.dumps(result))
        elif key and first:
            print(result)
        else:
            print(json.dumps(result))


if __name__ == "__main__":
    fire.Fire(handle_run_query2json)
