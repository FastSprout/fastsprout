A publisher may return several events. `@pub` publishes each returned `HeroEvent`; passing those events to `bus.get(*events)` retrieves their states as an `EventStatesGroup`.

## Result

The group contains three states for Spider-Man, Batman, and SuperMan:

```text
Event States: 3
```
