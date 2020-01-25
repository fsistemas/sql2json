import calendar
from datetime import timedelta

from dateutil.relativedelta import relativedelta

DATE_FIELDS = [
    "CURRENT_DATE",
    "START_CURRENT_MONTH",
    "END_CURRENT_MONTH",
    "START_CURRENT_YEAR",
    "END_CURRENT_YEAR",
]


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def first_day_month(current_date):
    return current_date.replace(day=1)


def first_day_year(current_date):
    return current_date.replace(day=1).replace(month=1)


def last_day_year(current_date):
    return current_date.replace(day=31).replace(month=12)


def last_day_month(current_date):
    month_last_day = calendar.monthrange(current_date.year, current_date.month)[1]

    return current_date.replace(day=month_last_day)


def parse_field(field, to_add, current_date, date_format="%Y-%m-%d"):
    if "CURRENT_DATE" == field:
        return (current_date + timedelta(days=to_add)).strftime(date_format)
    elif "START_CURRENT_MONTH" == field:
        return (first_day_month(current_date) + relativedelta(months=to_add)).strftime(
            date_format
        )
    elif "END_CURRENT_MONTH" == field:
        return (last_day_month(current_date) + relativedelta(months=to_add)).strftime(
            date_format
        )
    elif "START_CURRENT_YEAR" == field:
        return (first_day_year(current_date) + relativedelta(years=to_add)).strftime(
            date_format
        )
    elif "END_CURRENT_YEAR" == field:
        return (last_day_year(current_date) + relativedelta(years=to_add)).strftime(
            date_format
        )
    else:
        return field


def parse_formula(formula, current_date, date_format="%Y-%m-%d"):
    if any(ext in formula for ext in DATE_FIELDS):
        if "+" in formula:
            parts = formula.split("+")

            return parse_field(
                parts[0].strip(), int(parts[1]), current_date, date_format
            )
        elif "-" in formula:
            parts = formula.split("-")
            return parse_field(
                parts[0].strip(), -int(parts[1]), current_date, date_format
            )

    return parse_field(formula.strip(), 0, current_date, date_format)


def parse_parameter(param_value, current_date, format_separator="|"):
    if not param_value:
        return param_value
    elif is_number(param_value):
        return param_value
    elif format_separator in str(param_value):
        field, date_format = param_value.split(format_separator)

        return parse_formula(field, current_date, date_format.strip())
    else:
        return parse_formula(param_value, current_date)
