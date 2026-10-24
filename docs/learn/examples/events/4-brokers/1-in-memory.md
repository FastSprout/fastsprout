# 1. In Memory

<!-- example-source: examples/events/04_brokers/01_in_memory.py -->

Collect subscriber results from the local Bubus-backed broker.

InMemoryBroker is the default EventBus backend. It delivers events in the
current process without an external server. Waiting on the published state
collects all subscriber results.

## Source

```{.python}
--8<-- "examples/events/04_brokers/01_in_memory.py"
```

## Result

```text
Handled orders: [42]
Pending handlers: 0
```
