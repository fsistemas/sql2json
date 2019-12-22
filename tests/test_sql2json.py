from sql2json import __version__
from sql2json import run_query_by_name
import json

def test_version():
    assert __version__ == '0.1.1'


def test_run_query_by_name_empty_param():
    json_results = run_query_by_name()
    json_result = json_results[0]

    assert 1 == json_result["a"]
    assert 2 == json_result["b"]

def test_run_query_by_name_default_defalt_name():
    json_results = run_query_by_name("default")
    json_result = json_results[0]

    assert 1 == json_result["a"]
    assert 2 == json_result["b"]

def test_run_query_by_name_default_defalt_name():
    json_results = run_query_by_name(query_name="default")
    json_result = json_results[0]

    assert 1 == json_result["a"]
    assert 2 == json_result["b"]

def test_run_query_by_name_default():
    json_results = run_query_by_name("default", "default")
    json_result = json_results[0]

    assert 1 == json_result["a"]
    assert 2 == json_result["b"]
