# 7. Middleware

`EventsMiddleware` runs `SimpleMiddlewareForFirstEvent` only for `FirstEvent`. The middleware receives the typed `EventState` and can await its handler result. `SecondEvent` is published by the same action but does not use this middleware.

Run from the repository root:

```bash
uv run --extra events python examples/events/07_middleware.py
```

## Source

```python
--8<-- "examples/events/07_middleware.py"
```

1. `wait()` returns the results collected for this particular event state.
2. The wrapper inspects the middleware's typed `EventState` parameter to select events.

## Result

The middleware prints:

```text
Event State: FirstEvent
EventResult[FirstEvent]: ([], [])
```

The result has no returned values or pending handlers because the subscriber returns `None`.
