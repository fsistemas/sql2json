import datetime
from sql2json.parameter import parse_field, parse_formula, parse_parameter


def test_parse_field_current_date_ymd():
    current_date = datetime.datetime.strptime('2019-12-30', '%Y-%m-%d').date()

    assert '2019-12-30' == parse_field('CURRENT_DATE', 0, current_date)
    assert '2019-12-31' == parse_field('CURRENT_DATE', 1, current_date)
    assert '2019-12-31 00:00:00' == parse_field('CURRENT_DATE', 1, current_date, date_format='%Y-%m-%d 00:00:00')
    assert '2019-12-31 23:59:59' == parse_field('CURRENT_DATE', 1, current_date, date_format='%Y-%m-%d 23:59:59')


def test_parse_field_start_current_month_ymd():
    current_date = datetime.datetime.strptime('2019-12-30', '%Y-%m-%d').date()

    assert '2019-12-01' == parse_field('START_CURRENT_MONTH', 0, current_date)
    assert '2020-01-01' == parse_field('START_CURRENT_MONTH', 1, current_date)
    assert '2020-01-01 00:00:00' == parse_field('START_CURRENT_MONTH', 1, current_date, date_format='%Y-%m-%d 00:00:00')
    assert '2020-01-01 23:59:59' == parse_field('START_CURRENT_MONTH', 1, current_date, date_format='%Y-%m-%d 23:59:59')


def test_parse_field_end_current_month_ymd():
    current_date = datetime.datetime.strptime('2019-12-30', '%Y-%m-%d').date()

    assert '2019-12-31' == parse_field('END_CURRENT_MONTH', 0, current_date)
    assert '2020-01-31' == parse_field('END_CURRENT_MONTH', 1, current_date)
    assert '2019-11-30 00:00:00' == parse_field('END_CURRENT_MONTH', -1, current_date, date_format='%Y-%m-%d 00:00:00')
    assert '2019-11-30 23:59:59' == parse_field('END_CURRENT_MONTH', -1, current_date, date_format='%Y-%m-%d 23:59:59')


def test_parse_formula_current_date_ymd():
    current_date = datetime.datetime.strptime('2019-12-30', '%Y-%m-%d').date()

    assert '2019-12-30' == parse_formula('CURRENT_DATE', current_date)
    assert '2019-12-31' == parse_formula('CURRENT_DATE+1', current_date)
    assert '2019-12-31 00:00:00' == parse_formula('CURRENT_DATE + 1', current_date, date_format='%Y-%m-%d 00:00:00')
    assert '2019-12-31 23:59:59' == parse_formula('CURRENT_DATE + 1', current_date, date_format='%Y-%m-%d 23:59:59')


def test_parse_formula_start_current_month_ymd():
    current_date = datetime.datetime.strptime('2019-12-30', '%Y-%m-%d').date()

    assert '2019-12-01' == parse_formula('START_CURRENT_MONTH', current_date)
    assert '2020-01-01' == parse_formula('START_CURRENT_MONTH+1', current_date)
    assert '2020-01-01 00:00:00' == parse_formula('START_CURRENT_MONTH+1', current_date, date_format='%Y-%m-%d 00:00:00')
    assert '2020-01-01 23:59:59' == parse_formula('START_CURRENT_MONTH + 1', current_date, date_format='%Y-%m-%d 23:59:59')


def test_parse_formula_end_current_month_ymd():
    current_date = datetime.datetime.strptime('2019-12-30', '%Y-%m-%d').date()

    assert '2019-12-31' == parse_formula('END_CURRENT_MONTH', current_date)
    assert '2020-01-31' == parse_formula('END_CURRENT_MONTH+1', current_date)
    assert '2019-11-30 00:00:00' == parse_formula('END_CURRENT_MONTH-1', current_date, date_format='%Y-%m-%d 00:00:00')
    assert '2019-11-30 23:59:59' == parse_formula('END_CURRENT_MONTH - 1 ', current_date, date_format='%Y-%m-%d 23:59:59')


def test_parse_parameter_current_date_ymd():
    current_date = datetime.datetime.strptime('2019-12-30', '%Y-%m-%d').date()

    assert '2019-12-30' == parse_parameter('CURRENT_DATE', current_date)
    assert '2019-12-31' == parse_formula('CURRENT_DATE+1', current_date)
    assert '2019-12-31 00:00:00' == parse_formula('CURRENT_DATE + 1', current_date, date_format='%Y-%m-%d 00:00:00')
    assert '2019-12-31 23:59:59' == parse_formula('CURRENT_DATE + 1', current_date, date_format='%Y-%m-%d 23:59:59')


def test_parse_parameter_start_current_month_ymd():
    current_date = datetime.datetime.strptime('2019-12-30', '%Y-%m-%d').date()

    assert '2019-12-01' == parse_parameter('START_CURRENT_MONTH', current_date)
    assert '2020-01-01' == parse_parameter('START_CURRENT_MONTH+1', current_date)
    assert '2020-01-01 00:00:00' == parse_parameter('START_CURRENT_MONTH+1|%Y-%m-%d 00:00:00', current_date)
    assert '2020-01-01 23:59:59' == parse_parameter('START_CURRENT_MONTH + 1 | %Y-%m-%d 23:59:59', current_date)


def test_parse_parameter_end_current_month_ymd():
    current_date = datetime.datetime.strptime('2019-12-30', '%Y-%m-%d').date()

    assert '2019-12-31' == parse_parameter('END_CURRENT_MONTH', current_date)
    assert '2020-01-31' == parse_parameter('END_CURRENT_MONTH+1', current_date)
    assert '2019-11-30 00:00:00' == parse_parameter('END_CURRENT_MONTH-1 | %Y-%m-%d 00:00:00', current_date)
    assert '2019-11-30 23:59:59' == parse_parameter('END_CURRENT_MONTH - 1 | %Y-%m-%d 23:59:59', current_date)
