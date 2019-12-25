==============
sql2json usage
==============

sql2json is a tool to query a sql database and write an output in JSON format in standard output.

sql2json install
================

* **python3**: pip3 install sql2json

sql2json config file
====================

sql2json needs a json config file located at USER_HOME/.sql2json/config.json with the structure:

If you does not have config.json file sql2json asumes this one to allow you do some testing

.. code-block:: json

    {
        "conections": {
            "default": "sqlite:///test.db"
        },
        "queries": {
            "default": "SELECT 1 AS a, 2 AS b"
        }
    }

* conections: Is a dict, the key is our conection name and value is a sqlalchemy valid conection string
* queries: Is a dict, the key is our query name and value is a sql query

**IMPORTANT**: You nedd to install in your own the specific driver of your database.

If you need to know the specific conection string for your database, it's the sqlalchemy oficial documentation: https://docs.sqlalchemy.org/en/13/core/engines.html

sql2json usage
==============

* Run the query named "default" in test conection "default" without a config file(USER_HOME/.sql2json/config.json): **python3 -m sql2json**

**Result**:

.. code-block:: json

    [
        {
            "a": 1,
            "b": 2
        }
    ]

* Run query named "my_test_query", conection named "my_conection" in sql2json config file(USER_HOME/.sql2json/config.json): **python3 -m sql2json --name my_conection  --query my_test_query**

* Run custom query from command line: **python3 -m sql2json --query "SELECT 100 AS totalSalesMonth"**

**Result**:

.. code-block:: json

    [
        {
            "totalSalesMonth": 100
        }
    ]

* Run custom query from command line, only first object in result: **python3 -m sql2json --first --query "SELECT 100 AS totalSalesMonth"**

**Result**:

.. code-block:: json

    {
        "totalSalesMonth": 100
    }

* Run custom query from command line, only the value of a column on first object in result: **python3 -m sql2json --first --key totalSalesMonth --query "SELECT 100 AS totalSalesMonth"**

**Result**: 100

* Run query in custom conection from command line(I recomend you have database conection in config file): **python3 -m sql2json --query "SELECT 100 AS totalSalesMonth" --first --key --name "sqlite:///test.db"**

**Result**: 100

* Run query with parameters: **python3 -m sql2json --query "SELECT 100 AS totalSalesMonth, :b AS b, :b + 1 AS b1, :x AS x, :x + :b AS xb" --first --b 5 -x 2**

**Result**:

.. code-block:: json

    {
        "totalSalesMonth": 100,
        "b": 5,
        "b1": 6,
        "x": 2,
        "xb": 7
    }
