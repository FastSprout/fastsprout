# 1. Middleware

<!-- example-source: examples/events/03_bus/01_middleware.py -->

Run middleware for one event type and inspect its handler result.

## Source

```{.python}
--8<-- "examples/events/03_bus/01_middleware.py"
```

## Result

```text
Event State: EventState(event=FirstEvent())
EventResult[FirstEvent]: EventResult(state=EventState(event=FirstEvent()), values=[], pending=0, errors=[])
```
