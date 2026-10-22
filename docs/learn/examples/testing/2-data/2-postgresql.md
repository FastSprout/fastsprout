# 2. PostgreSQL

<!-- example-source: examples/testing/02_data/02_postgresql.py -->

Run the same DataR operations against PostgreSQL in a disposable container.

Run this example with Docker using pytest -m integration.
TestPostgreSQL reuses the SQL context's table, session, and binding lifecycle.
Pass a configured PostgresContainer and engine/session factories for native
configuration; the default image is the public postgres image.

## Source

```{.python}
--8<-- "examples/testing/02_data/02_postgresql.py"
```

## Result

```text
No tests selected by -m 'not integration'.
```
