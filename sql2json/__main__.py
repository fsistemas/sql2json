from __future__ import print_function

import click
import json

from .sql2json import run_query_by_name

@click.command()
@click.option("--name", default="default", help="Conexion name.")
@click.option("--query", default="default", help="Query name.")
def handle_run_query2json(name='default', query='default'):
    results = run_query_by_name(name, query)
    print(json.dumps(results))

if __name__ == "__main__":
    handle_run_query2json()
