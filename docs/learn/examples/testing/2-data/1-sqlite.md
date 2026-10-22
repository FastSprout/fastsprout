# 1. SQLite

<!-- example-source: examples/testing/02_data/01_sqlite.py -->

Reuse an isolated SQLite database across committed DataR operations.

TestSQLite creates the selected tables and binds their signpost for the context.
It removes the tables and restores previous bindings on exit, including after
an exception. Pass an engine or a session factory for SQLAlchemy configuration.

Pytest runs database, created_hero, and test_get through fixture dependencies.
The database context stays open until the test finishes.

## Source

```{.python}
--8<-- "examples/testing/02_data/01_sqlite.py"
```

## Result

```text

examples/testing/02_data/01_sqlite.py::test_get PASSED                   [100%]
```
