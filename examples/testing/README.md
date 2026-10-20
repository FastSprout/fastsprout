# TESTING Examples

Pytest fixtures and tests declare typed BDD phases. Share cases
through fixtures and base classes; property tests use Hypothesis. SQLite
contexts prepare isolated tables and restore entity bindings after each test.
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
