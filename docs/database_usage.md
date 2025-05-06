# Using a Test Database with Cover Agent
Note: This feature is still in beta

## Requirements
Currently, only SQLite is supported. [SQLite](https://www.sqlite.org/) uses a local `.db` file to write to and read from (versus a server based database). The long term goal is to use any type of database that is support by [SQLAlchemy](https://www.sqlalchemy.org/).

You'll need to have SQLite installed in order to view the tables but to get started you can just create an empty `.db` file using the `touch` command. For example:
```
touch run_tests.db
```

## Running with an external DB
You can run Cover Agent using the `--log-db-path` option. For example:
```
cover-agent \
  --source-file-path "templated_tests/python_fastapi/app.py" \
  --test-file-path "templated_tests/python_fastapi/test_app.py" \
  --code-coverage-report-path "templated_tests/python_fastapi/coverage.xml" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --test-command-dir "templated_tests/python_fastapi" \
  --coverage-type "cobertura" \
  --desired-coverage 70 \
  --max-iterations 10 \
  --suppress-log-files \
  --log-db-path "run_tests.db"
```

Cover Agent will create a table called `unit_test_generation_attempts` within the database.

## Integration Tests
You can run the integration test suite and pass in the local `.db` to each Docker container with the following (example) command at the root of this repository:
```
LOG_DB_PATH="<full_path_to_root_folder>/run_tests.db" tests_integration/test_all.sh
```

## Observing the test data
You can look at the test results using an external database reader or the basic SQLite command line tool:
```
sqlite3 run_tests.db
```

Once in SQLite you can show the tables and observe that after running some tests a table called `unit_test_generation_attempts` has been created:
```
sqlite> .tables
unit_test_generation_attempts
```

To get the definition of our table we can run:
```
sqlite> PRAGMA table_info(unit_test_generation_attempts);
0|id|INTEGER|1||1
1|run_time|DATETIME|0||0
2|status|VARCHAR|0||0
3|reason|TEXT|0||0
4|exit_code|INTEGER|0||0
5|stderr|TEXT|0||0
6|stdout|TEXT|0||0
7|test_code|TEXT|0||0
8|imports|TEXT|0||0
```

A simple `select * from unit_test_generation_attempts;` query will display all test results (which include formatted carriage returns). This may be a bit difficult to look at from the command line so using a GUI would probably serve you a bit better.

You can also filter the results to show only failed tests, for example:
```
sqlite> select * from unit_test_generation_attempts where status = "FAIL";
```