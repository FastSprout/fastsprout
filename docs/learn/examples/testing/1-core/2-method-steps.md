# 2. Method Steps

<!-- example-source: examples/testing/01_core/02_method_steps.py -->

Write pytest cases once and inherit them for different providers.

## Source

```{.python}
--8<-- "examples/testing/01_core/02_method_steps.py"
```

## Result

```text

examples/testing/01_core/02_method_steps.py::TestCart::test_cart_count[book] PASSED [ 25%]
examples/testing/01_core/02_method_steps.py::TestCart::test_cart_count[pen] PASSED [ 50%]
examples/testing/01_core/02_method_steps.py::TestCheckedCart::test_cart_count[book] PASSED [ 75%]
examples/testing/01_core/02_method_steps.py::TestCheckedCart::test_cart_count[pen] PASSED [100%]
```
