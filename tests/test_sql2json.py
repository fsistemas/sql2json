from sql2json import __version__, run_query_by_name


def test_version():
    assert __version__ == "0.1.10"


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


def test_run_query_by_name_default_defalt_query():
    json_results = run_query_by_name(query_name="default")
    json_result = json_results[0]

    assert 1 == json_result["a"]
    assert 2 == json_result["b"]


def test_run_query_by_name_default():
    json_results = run_query_by_name("default", "default")
    json_result = json_results[0]

    assert 1 == json_result["a"]
    assert 2 == json_result["b"]


def test_run_query_raw_sql():
    json_results = run_query_by_name("default", "SELECT 11 AS a, 22 AS b")
    json_result = json_results[0]

    assert 11 == json_result["a"]
    assert 22 == json_result["b"]


def test_run_query_raw_sql_parameters():
    x = 10
    y = 20

    query = "SELECT :x AS a, :y AS b, :x + :y AS xy"

    json_results = run_query_by_name("default", query, x=x, y=y)
    json_result = json_results[0]

    assert x == json_result["a"]
    assert y == json_result["b"]
    assert x + y == json_result["xy"]
