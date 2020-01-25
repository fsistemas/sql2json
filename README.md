# Sql2json: sql2json is a tool to query a sql database and write result in JSON format in standard output

sql2json help you to automate repetitive tasks.
For example i need a cronjob to extract yesterday sales and sent it to geckoboard.

This tool is focused to use to automate command line apps or cron jobs to extract data from sql databases

## How install sql2json
* **python3**: pip3 install sql2json

## sql2json config file

sql2json by default use a config file located at USER_HOME/.sql2json/config.json

config.json structure:

```
{
    "conections": {
        "default": "sqlite:///test.db",
        "postgress": "postgresql://scott:tiger@localhost:5432/mydatabase",
        "mysql": "mysql://scott:tiger@localhost/foo"
    },
    "queries": {
        "default": "SELECT 1 AS a, 2 AS b",
        "sales_month_since": "SELECT inv.month, SUM(inv.amount) AS sales FROM invoices inv WHERE inv.date >= :date_from ",
        "total_sales_since": "SELECT SUM(inv.amount) AS sales FROM invoices inv WHERE inv.date >= :date_from ",
        "long_query": "@FULL_PATH_TO_SQL_FILE",
		"json": "SELECT JSON_OBJECT('id', 87, 'name', 'carrot') AS json",
		"jsonarray": "SELECT JSON_ARRAY(1, 'abc', NULL, TRUE) AS jsonarray, JSON_OBJECT('id', 87, 'name', 'carrot') AS jsonobject",
        "operation_parameters": "@/Users/myusername/myproject/my-super-query.sql"
    }
}
```

## Use a config.json in a different path

You can use sql2json --config PATH_TO_YOUR_CONFIG_FILE

## Available variables to do your life easy:
- START_CURRENT_MONTH: Date the first day of current month
- CURRENT_DATE: Current Date
- END_CURRENT_MONTH: Date the last day of current month
- START_CURRENT_YEAR: First day of current year
- END_CURRENT_YEAR: First day of current year

## Operations in variables
- You can use + or - operator in your querys with variables CURRENT_DATE, START_CURRENT_MONTH, END_CURRENT_MONTH
- +1, -1 in CURRENT_DATE mean +1 day, -1 day
- +1, -1 in START_CURRENT_MONTH, END_CURRENT_MONTH mean +1 month, -1 month
- +1, -1 in START_CURRENT_YEAR, END_CURRENT_YEAR mean +1 year, -1 year

## Date formats to CURRENT_DATE, START_CURRENT_MONTH, END_CURRENT_MONTH, START_CURRENT_YEAR, END_CURRENT_YEAR
You can use date format supported by python datetime.strftime function, default is %Y-%m-%d

## How to run queries using sql2json:

### Run query sales_month in database conection mysql:

python3 -m sql2json --name mysql --query sales_month_since --date_from "START_CURRENT_MONTH-1"

Output:

```
[
    {
        "month": "January",
        "sales": 5000
    },
    {
        "month": "February",
        "sales": 3000
    }
]
```

### I don't wat an array, i want an object with an atribute with the results, useful to generate in format to post to geckoboard

python3 -m sql2json --name mysql --query sales_month_since --date_from "START_CURRENT_MONTH-1" --wrapper

Output:

```
{
    "data": [
        {
            "month": "January",
            "sales": 5000
        },
        {
            "month": "February",
            "sales": 3000
        }
    ]
}
```

### Run query sales_month in database conection mysql, use month as key, sales as value:

python3 -m sql2json --name mysql --query sales_month_since --date_from "START_CURRENT_MONTH-1" --key month --value sales

Output:

```
[
    {
        "January": 5000
    },
    {
        "sales": 3000
    }
]
```

### Run query sales_month in database conection mysql, get the unique row and only sales amount:

python3 -m sql2json --name mysql --query total_sales_since --date_from "CURRENT_DATE-10" --first --key sales

Output: 500 or the amount of money you sold since 10 days ago

### When i use sql2json with result of JSON functions i get escaped strings as value

sql2json as a flag to allow you specify your JSON columns

python3 -m sql2json --name mysql --query json --jsonkeys "json, jsonarray"

Result:

```
[
    {
        "json": {
            "id":  87,
            "name", "carrot"
        }
        "jsonarray": [1, "abc", null, true],
    }
]
```

This is only a row i want first row only, no array.

python3 -m sql2json --name mysql --query json --jsonkeys "json, jsonarray" --first

Result:

```
    {
        "json": {
            "id":  87,
            "name", "carrot"
        }
        "jsonarray": [1, "abc", null, true],
    }
```

### Run query in external sql file:

query "operation_parameters"
Path "Users/myusername/myproject/my-super-query.sql"

Content of my-super-query.sql:

```
SELECT p.name, p.age
FROM persons p
WHERE p.age > :min_age
AND p.creation_date > :min_date
ORDER BY p.age DESC
LIMIT 10
```

min_age: 18
min_date: Today YYYY-MM-DD 00:00:00

python3 -m sql2json --name mysql --query operation_parameters --min_age 18 --min_date CURRENT_DATE|%Y-%m-%d 00:00:00

min_age: 18
min_date: First day, current year YYYY-01-01 00:00:00

python3 -m sql2json --name mysql --query operation_parameters --min_age 18 --min_date START_CURRENT_YEAR|%Y-%m-%d 00:00:00

### Run external SQL query not defined in config file

python3 -m sql2json --name mysql --query "@/Users/myusername/myproject/my-super-query.sql" --min_age 18 --min_date START_CURRENT_YEAR|%Y-%m-%d 00:00:00

### Run custom query inline

You do't need to have all your queries in config file

python3 -m sql2json --name mysql --query "SELECT NOW() AS date" --first --key date
