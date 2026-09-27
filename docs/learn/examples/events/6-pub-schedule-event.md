# 6. Pub Schedule Event

`@pub(on="* * * * * *")` schedules a publisher for every second while `bus.scheduler()` is active. The example keeps the scheduler open long enough for one tick and waits for the resulting event.

Run from the repository root:

```bash
uv run --extra events python examples/events/06_pub_schedule_event.py
```

## Source

```python
--8<-- "examples/events/06_pub_schedule_event.py"
```

## Result

The subscriber prints a Spider-Man event, followed by its result:

```text
HeroEvent: name='Spider-Man' power='spider'
Event Result: Spider-Man
```
