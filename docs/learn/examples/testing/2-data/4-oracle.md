# 4. Oracle

<!-- example-source: examples/testing/02_data/04_oracle.py -->

Run DataR operations against Oracle Free with an asynchronous driver.

Run this example with Docker using pytest -m integration. TestOracle
starts an Oracle Free container, prepares the selected tables, and restores
entity bindings on exit. A configured OracleDbContainer selects credentials
and the service; engine and session factories retain native configuration.
Oracle VARCHAR2 columns require an explicit length, set here on the name field.

## Source

```{.python}
--8<-- "examples/testing/02_data/04_oracle.py"
```

## Result

```text
No tests selected by -m 'not integration'.
```
