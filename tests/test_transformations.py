"""
Unit tests for run_query2json output transformations and the helpers it uses.

These run in-process against an in-memory SQLite database (no config file
needed: an explicit connection string and inline SQL are passed straight
through). They cover first/key/value/wrapper/jsonkeys shapes, SQL-file loading,
and the small result-shaping helpers in sql2json.sql2json.
"""

import json

import pytest

from sql2json import run_query2json
from sql2json.sql2json import (
    get_for_key_or_first_map_value,
    load_query_from_file,
    parse_json_columns,
)

MEMORY = "sqlite:///:memory:"
TWO_ROWS = (
    "SELECT 'January' AS month, 5000 AS sales " "UNION ALL SELECT 'February', 3000"
)
NO_ROWS = "SELECT 'x' AS month, 1 AS sales WHERE 1 = 0"


class TestDefaultShape:
    def test_returns_list_of_rows(self):
        rows = run_query2json(name=MEMORY, query=TWO_ROWS)
        assert rows == [
            {"month": "January", "sales": 5000},
            {"month": "February", "sales": 3000},
        ]


class TestFirst:
    def test_first_returns_single_row(self):
        result = run_query2json(name=MEMORY, query=TWO_ROWS, first=True)
        assert result == {"month": "January", "sales": 5000}

    def test_first_with_key_extracts_scalar(self):
        result = run_query2json(name=MEMORY, query=TWO_ROWS, first=True, key="sales")
        assert result == 5000

    def test_first_with_key_and_value_makes_single_pair(self):
        result = run_query2json(
            name=MEMORY, query=TWO_ROWS, first=True, key="month", value="sales"
        )
        assert result == {"January": 5000}

    def test_first_on_empty_with_key_returns_empty_string(self):
        result = run_query2json(name=MEMORY, query=NO_ROWS, first=True, key="sales")
        assert result == ""

    def test_first_on_empty_without_key_returns_empty_dict(self):
        result = run_query2json(name=MEMORY, query=NO_ROWS, first=True)
        assert result == {}


class TestKeyValue:
    def test_key_only_extracts_column_values(self):
        result = run_query2json(name=MEMORY, query=TWO_ROWS, key="month")
        assert result == ["January", "February"]

    def test_key_and_value_makes_pairs(self):
        result = run_query2json(name=MEMORY, query=TWO_ROWS, key="month", value="sales")
        assert result == [{"January": 5000}, {"February": 3000}]


class TestWrapper:
    def test_wrapper_wraps_list_in_data(self):
        result = run_query2json(name=MEMORY, query=TWO_ROWS, wrapper=True)
        assert result == {
            "data": [
                {"month": "January", "sales": 5000},
                {"month": "February", "sales": 3000},
            ]
        }

    def test_wrapper_with_first(self):
        result = run_query2json(name=MEMORY, query=TWO_ROWS, wrapper=True, first=True)
        assert result == {"data": {"month": "January", "sales": 5000}}


class TestJsonKeys:
    def test_string_column_is_parsed_into_object(self):
        query = 'SELECT \'{"x": 1, "y": [2, 3]}\' AS payload'
        result = run_query2json(name=MEMORY, query=query, jsonkeys="payload")
        assert result == [{"payload": {"x": 1, "y": [2, 3]}}]

    def test_unlisted_columns_are_left_untouched(self):
        query = "SELECT '{\"x\": 1}' AS payload, 'plain' AS note"
        result = run_query2json(name=MEMORY, query=query, jsonkeys="payload")
        assert result == [{"payload": {"x": 1}, "note": "plain"}]

    def test_malformed_json_raises(self):
        # Documents current behavior: invalid JSON in a jsonkeys column surfaces
        # as a normal exception from the library API.
        query = "SELECT 'not valid json' AS payload"
        with pytest.raises(json.JSONDecodeError):
            run_query2json(name=MEMORY, query=query, jsonkeys="payload")


class TestSqlFile:
    def test_query_loaded_from_at_path(self, tmp_path):
        sql_file = tmp_path / "query.sql"
        sql_file.write_text("SELECT :answer AS answer")
        result = run_query2json(name=MEMORY, query=f"@{sql_file}", answer=123)
        assert result == [{"answer": 123}]


class TestLoadQueryFromFile:
    def test_reads_plain_path(self, tmp_path):
        sql_file = tmp_path / "q.sql"
        sql_file.write_text("SELECT 1")
        assert load_query_from_file(str(sql_file)) == "SELECT 1"

    def test_strips_leading_at(self, tmp_path):
        sql_file = tmp_path / "q.sql"
        sql_file.write_text("SELECT 2")
        assert load_query_from_file(f"@{sql_file}") == "SELECT 2"


class TestParseJsonColumns:
    def test_no_jsonkeys_returns_input_unchanged(self):
        row = {"a": '{"x": 1}'}
        assert parse_json_columns(row, "") == row

    def test_tuple_jsonkeys_supported(self):
        row = {"payload": '{"x": 1}'}
        assert parse_json_columns(row, ("payload",)) == {"payload": {"x": 1}}

    def test_non_str_non_tuple_jsonkeys_returns_input_unchanged(self):
        # jsonkeys of an unexpected type yields no keys to parse.
        row = {"payload": '{"x": 1}'}
        assert parse_json_columns(row, None) == row


class TestGetForKeyOrFirstMapValue:
    def test_returns_value_for_present_key(self):
        assert get_for_key_or_first_map_value({"a": 1, "b": 2}, "b") == 2

    def test_returns_first_value_when_key_absent(self):
        assert get_for_key_or_first_map_value({"a": 1, "b": 2}, "missing") == 1

    def test_returns_empty_string_for_empty_dict(self):
        assert get_for_key_or_first_map_value({}, "anything") == ""
