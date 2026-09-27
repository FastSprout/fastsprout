# 1. Pub Event

`@pub` publishes the event returned by an action. After calling `return_hero()`, the example asks the same bus for the returned event's `EventState`.

Run from the repository root:

```bash
uv run --extra events python examples/events/01_pub_event.py
```

## Source

```python
--8<-- "examples/events/01_pub_event.py"
```

## Result

`bus.get(e)` finds a state whose event is Spider-Man:

```text
Event State: Spider-Man
```
