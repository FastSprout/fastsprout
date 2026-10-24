# 3. Result Schema

<!-- example-source: examples/events/03_bus/03_result_schema.py -->

Wait for a receipt from one event while retaining other subscriber results.

Passing a schema to state.wait() selects matching results. Without a schema,
wait() returns every subscriber's result. A timeout leaves pending work running.

## Source

```{.python}
--8<-- "examples/events/03_bus/03_result_schema.py"
```

## Result

```text
R-42
Subscriber results: 2
```
