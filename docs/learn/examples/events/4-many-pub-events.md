# 4. Many Pub Events

A publisher may return several events. `@pub` publishes each returned `HeroEvent`; passing those events to `bus.get(*events)` retrieves their states as an `EventStatesGroup`.

Run from the repository root:

```bash
uv run --extra events python examples/events/04_many_pub_events.py
```

## Source

```python
--8<-- "examples/events/04_many_pub_events.py"
```

## Result

The group contains three states for Spider-Man, Batman, and SuperMan:

```text
Event States: 3
```
