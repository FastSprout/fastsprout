# 2. In Memory

<!-- example-source: examples/testing/03_events/02_in_memory.py -->

Test multiple subscribers with the local Bubus-backed broker.

The given fixture owns the broker, when publishes an event and waits for its
subscribers, and then checks their results. Pytest closes the broker after
the assertion, including when the test fails. No Docker server is required.

## Source

```{.python}
--8<-- "examples/testing/03_events/02_in_memory.py"
```

## Result

```text

examples/testing/03_events/02_in_memory.py::test_subscriber_results PASSED [100%]
```
