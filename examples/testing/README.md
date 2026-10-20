# TESTING Examples

Pytest fixtures and tests declare typed BDD phases. Share cases
through fixtures and base classes; property tests use Hypothesis. Database
contexts prepare isolated tables and restore entity bindings. Run PostgreSQL,
MySQL, MariaDB, and Oracle examples with Docker using pytest -m integration.
Run from the repository root:

```bash
uv run --extra testing-data pytest -p fastsprout.testing.core.plugin -o addopts= examples/testing/01_core/01_function_steps.py
```

## 1. Core

| File | Shows |
| --- | --- |
| [01_core/01_function_steps.py](01_core/01_function_steps.py) | Parse step texts into typed pytest parameters. |
| [01_core/02_method_steps.py](01_core/02_method_steps.py) | Write pytest cases once and inherit them for different providers. |
| [01_core/03_properties.py](01_core/03_properties.py) | Run typed Hypothesis properties through pytest. |

## 2. Data

| File | Shows |
| --- | --- |
| [02_data/01_sqlite.py](02_data/01_sqlite.py) | Reuse an isolated SQLite database across committed DataR operations. |
| [02_data/02_postgresql.py](02_data/02_postgresql.py) | Run the same DataR operations against PostgreSQL in a disposable container. |
| [02_data/03_mysql.py](02_data/03_mysql.py) | Run one reusable test against MySQL and MariaDB containers. |
| [02_data/04_oracle.py](02_data/04_oracle.py) | Run DataR operations against Oracle Free with an asynchronous driver. |
