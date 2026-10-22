# 1. Function Steps

<!-- example-source: examples/testing/01_core/01_function_steps.py -->

Parse step texts into typed pytest parameters.

Use `{name}` for strings, `{name:d}` for integers, and `{name:f}` for floats.
Fixture dependencies determine execution order.

## Source

```{.python}
--8<-- "examples/testing/01_core/01_function_steps.py"
```

## Result

```text

examples/testing/01_core/01_function_steps.py::test_cart_count[book] PASSED [ 50%]
examples/testing/01_core/01_function_steps.py::test_cart_count[pen] PASSED [100%]
```
