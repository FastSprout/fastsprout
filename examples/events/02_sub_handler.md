`@sub(HeroEvent)` registers a handler for that event type. `bus.publish()` returns an `EventState`; awaiting `state.wait()` waits for the subscribed handler and returns its `EventResult`.

## Result

The handler prints:

```text
HeroEvent: name='Batman' power='money'
Event Result: ([], [])
```

The result contains no returned values or pending handlers because the subscriber returns `None`.
