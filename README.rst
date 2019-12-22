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

IMPORTANT: You nedd to install in your own the specific driver of your database.

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

* Run query named "my_conection", conection named "my_test_query" in sql2json config file(USER_HOME/.sql2json/config.json): **python3 -m sql2json --name my_conection  --query my_test_query**
