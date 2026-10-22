# 3. MySQL

<!-- example-source: examples/testing/02_data/03_mysql.py -->

Run one reusable test against MySQL and MariaDB containers.

Run both cases with Docker using pytest -m integration. The contexts
share SQL table setup, signpost binding, and cleanup. Pass a configured
MySqlContainer or engine/session factories to change native settings.

## Source

```{.python}
--8<-- "examples/testing/02_data/03_mysql.py"
```

## Result

```text
No tests selected by -m 'not integration'.
```
