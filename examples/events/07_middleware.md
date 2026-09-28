`EventsMiddleware` runs `SimpleMiddlewareForFirstEvent` only for `FirstEvent`. The middleware receives the typed `EventState` and can await its handler result. `SecondEvent` is published by the same action but does not use this middleware.

## Annotations

1. `wait()` returns the results collected for this particular event state.
2. The wrapper inspects the middleware's typed `EventState` parameter to select events.

## Result

The middleware prints the event state and its result. The result has no returned
values or pending handlers because the subscriber returns `None`.

```text
Event State: EventState(event=FirstEvent())
EventResult[FirstEvent]: EventResult(state=EventState(event=FirstEvent()), values=[], pending=0, errors=[])
```
