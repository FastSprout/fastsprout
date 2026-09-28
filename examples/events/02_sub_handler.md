`@sub(HeroEvent)` registers a handler for that event type. `bus.publish()` returns an `EventState`; awaiting `state.wait()` waits for the subscribed handler and returns its `EventResult`.

## Result

The handler prints the event and its result. The result contains no returned
values or pending handlers because the subscriber returns `None`.

```text
HeroEvent: name='Batman' power='money'
Event Result: EventResult(state=EventState(event=HeroEvent(name='Batman', power='money')), values=[], pending=0, errors=[])
```
