import datetime

import sql2json.parameter as parameter_api
from sql2json.parameter import parse_parameter
from sql2json.parameter import parameter_parser as parser


def test_parameter_public_surface_only_exports_parse_parameter():
    assert parameter_api.__all__ == ["parse_parameter"]
    assert parameter_api.parse_parameter is parse_parameter
    for private_name in (
        "is_number",
        "first_day_month",
        "first_day_year",
        "last_day_month",
        "last_day_year",
        "parse_field",
        "parse_formula",
    ):
        assert not hasattr(parameter_api, private_name)


def test_parse_field():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()
    assert "2019-12-30" == parser._parse_field("2019-12-30", 0, current_date)
    assert "name" == parser._parse_field("name", 0, current_date)


def test_parse_field_current_date_ymd():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-30" == parser._parse_field("CURRENT_DATE", 0, current_date)
    assert "2019-12-31" == parser._parse_field("CURRENT_DATE", 1, current_date)
    assert "2019-12-31 00:00:00" == parser._parse_field(
        "CURRENT_DATE", 1, current_date, date_format="%Y-%m-%d 00:00:00"
    )
    assert "2019-12-31 23:59:59" == parser._parse_field(
        "CURRENT_DATE", 1, current_date, date_format="%Y-%m-%d 23:59:59"
    )


def test_parse_field_start_current_month_ymd():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-01" == parser._parse_field("START_CURRENT_MONTH", 0, current_date)
    assert "2020-01-01" == parser._parse_field("START_CURRENT_MONTH", 1, current_date)
    assert "2020-01-01 00:00:00" == parser._parse_field(
        "START_CURRENT_MONTH", 1, current_date, date_format="%Y-%m-%d 00:00:00"
    )
    assert "2020-01-01 23:59:59" == parser._parse_field(
        "START_CURRENT_MONTH", 1, current_date, date_format="%Y-%m-%d 23:59:59"
    )


def test_parse_field_end_current_month_ymd():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-31" == parser._parse_field("END_CURRENT_MONTH", 0, current_date)
    assert "2020-01-31" == parser._parse_field("END_CURRENT_MONTH", 1, current_date)
    assert "2019-11-30 00:00:00" == parser._parse_field(
        "END_CURRENT_MONTH", -1, current_date, date_format="%Y-%m-%d 00:00:00"
    )
    assert "2019-11-30 23:59:59" == parser._parse_field(
        "END_CURRENT_MONTH", -1, current_date, date_format="%Y-%m-%d 23:59:59"
    )


def test_parse_formula():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-30" == parser._parse_formula("2019-12-30", current_date)
    assert "2019-12-31" == parser._parse_formula("2019-12-31", current_date)
    assert "2019-12-31 00:00:00" == parser._parse_formula(
        "2019-12-31 00:00:00", current_date, date_format="%Y-%m-%d 00:00:00"
    )
    assert "2019-12-31 23:59:59" == parser._parse_formula(
        "2019-12-31 23:59:59", current_date, date_format="%Y-%m-%d 23:59:59"
    )
    assert "field1" == parser._parse_formula("field1", current_date)
    assert "55" == parser._parse_formula("55", current_date)


def test_parse_formula_current_date_ymd():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-30" == parser._parse_formula("CURRENT_DATE", current_date)
    assert "2019-12-31" == parser._parse_formula("CURRENT_DATE+1", current_date)
    assert "2019-12-31 00:00:00" == parser._parse_formula(
        "CURRENT_DATE + 1", current_date, date_format="%Y-%m-%d 00:00:00"
    )
    assert "2019-12-31 23:59:59" == parser._parse_formula(
        "CURRENT_DATE + 1", current_date, date_format="%Y-%m-%d 23:59:59"
    )


def test_parse_formula_start_current_month_ymd():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-01" == parser._parse_formula("START_CURRENT_MONTH", current_date)
    assert "2020-01-01" == parser._parse_formula("START_CURRENT_MONTH+1", current_date)
    assert "2020-01-01 00:00:00" == parser._parse_formula(
        "START_CURRENT_MONTH+1", current_date, date_format="%Y-%m-%d 00:00:00"
    )
    assert "2020/01/01 00:00:00" == parser._parse_formula(
        "START_CURRENT_MONTH+1", current_date, date_format="%Y/%m/%d 00:00:00"
    )
    assert "2020-01-01 23:59:59" == parser._parse_formula(
        "START_CURRENT_MONTH + 1", current_date, date_format="%Y-%m-%d 23:59:59"
    )


def test_parse_formula_end_current_month_ymd():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-31" == parser._parse_formula("END_CURRENT_MONTH", current_date)
    assert "2020-01-31" == parser._parse_formula("END_CURRENT_MONTH+1", current_date)
    assert "2019-11-30 00:00:00" == parser._parse_formula(
        "END_CURRENT_MONTH-1", current_date, date_format="%Y-%m-%d 00:00:00"
    )
    assert "2019-11-30 23:59:59" == parser._parse_formula(
        "END_CURRENT_MONTH - 1 ", current_date, date_format="%Y-%m-%d 23:59:59"
    )


def test_parse_parameter():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-30" == parse_parameter("2019-12-30", current_date)
    assert "2019-12-31" == parser._parse_formula("2019-12-31", current_date)
    assert "2019-12-31 00:00:00" == parser._parse_formula(
        "2019-12-31 00:00:00", current_date, date_format="%Y-%m-%d 00:00:00"
    )
    assert "2019-12-31 23:59:59" == parser._parse_formula(
        "2019-12-31 23:59:59", current_date, date_format="%Y-%m-%d 23:59:59"
    )

    assert "field1" == parse_parameter("field1", current_date)
    assert "55" == parse_parameter("55", current_date)
    assert "55.2" == parse_parameter("55.2", current_date)
    assert "" == parse_parameter("", current_date)
    assert parse_parameter(False, current_date) is False


def test_parse_parameter_current_date_ymd():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-30" == parse_parameter("CURRENT_DATE", current_date)
    assert "2019-12-31" == parser._parse_formula("CURRENT_DATE+1", current_date)
    assert "2019-12-31 00:00:00" == parser._parse_formula(
        "CURRENT_DATE + 1", current_date, date_format="%Y-%m-%d 00:00:00"
    )
    assert "2019-12-31 23:59:59" == parser._parse_formula(
        "CURRENT_DATE + 1", current_date, date_format="%Y-%m-%d 23:59:59"
    )


def test_parse_parameter_current_date_ymd_seperator_slash():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-30" == parse_parameter(
        "CURRENT_DATE,%Y-%m-%d", current_date, format_separator=","
    )
    assert "2019-12-30" == parse_parameter(
        "CURRENT_DATE:%Y-%m-%d", current_date, format_separator=":"
    )
    assert "2019-12-30" == parse_parameter(
        "CURRENT_DATE#%Y-%m-%d", current_date, format_separator="#"
    )


def test_parse_parameter_start_current_month_ymd():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-01" == parse_parameter("START_CURRENT_MONTH", current_date)
    assert "2020-01-01" == parse_parameter("START_CURRENT_MONTH+1", current_date)
    assert "2020-01-01 00:00:00" == parse_parameter(
        "START_CURRENT_MONTH+1|%Y-%m-%d 00:00:00", current_date
    )
    assert "2020-01-01 23:59:59" == parse_parameter(
        "START_CURRENT_MONTH + 1 | %Y-%m-%d 23:59:59", current_date
    )


def test_parse_parameter_end_current_month_ymd():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-31" == parse_parameter("END_CURRENT_MONTH", current_date)
    assert "2020-01-31" == parse_parameter("END_CURRENT_MONTH+1", current_date)
    assert "2019-11-30 00:00:00" == parse_parameter(
        "END_CURRENT_MONTH-1 | %Y-%m-%d 00:00:00", current_date
    )
    assert "2019-11-30 23:59:59" == parse_parameter(
        "END_CURRENT_MONTH - 1 | %Y-%m-%d 23:59:59", current_date
    )


def test_parse_parameter_start_current_month_year():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-01-01" == parse_parameter("START_CURRENT_YEAR", current_date)
    assert "2020-01-01" == parse_parameter("START_CURRENT_YEAR+1", current_date)
    assert "2020-01-01 00:00:00" == parse_parameter(
        "START_CURRENT_YEAR+1|%Y-%m-%d 00:00:00", current_date
    )
    assert "2020-01-01 23:59:59" == parse_parameter(
        "START_CURRENT_YEAR + 1 | %Y-%m-%d 23:59:59", current_date
    )


def test_parse_parameter_end_current_year_ymd():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()

    assert "2019-12-31" == parse_parameter("END_CURRENT_YEAR", current_date)
    assert "2020-12-31" == parse_parameter("END_CURRENT_YEAR+1", current_date)
    assert "2018-12-31 00:00:00" == parse_parameter(
        "END_CURRENT_YEAR-1 | %Y-%m-%d 00:00:00", current_date
    )
    assert "2018-12-31 23:59:59" == parse_parameter(
        "END_CURRENT_YEAR - 1 | %Y-%m-%d 23:59:59", current_date
    )


def test_is_number():
    assert parser._is_number("123")
    assert not parser._is_number("123A")
    assert not parser._is_number("B123")


def test_first_day_month():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()
    assert datetime.datetime.strptime(
        "2019-12-01", "%Y-%m-%d"
    ).date() == parser._first_day_month(current_date)


def test_last_day_month():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()
    assert datetime.datetime.strptime(
        "2019-12-31", "%Y-%m-%d"
    ).date() == parser._last_day_month(current_date)


def test_first_day_year():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()
    assert datetime.datetime.strptime(
        "2019-01-01", "%Y-%m-%d"
    ).date() == parser._first_day_year(current_date)


def test_last_day_year():
    current_date = datetime.datetime.strptime("2019-12-30", "%Y-%m-%d").date()
    assert datetime.datetime.strptime(
        "2019-12-31", "%Y-%m-%d"
    ).date() == parser._last_day_year(current_date)
