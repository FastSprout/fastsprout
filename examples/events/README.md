# EVENTS Examples

The events layer publishes events through EventBus, delivers them
to subscribers, tracks results, and runs scheduled publishers and middleware.
Run from the repository root with the events extra:

```bash
uv run --extra events python examples/events/01_pub_event.py
```

---

| File | Shows |
| --- | --- |
| [01_pub_event.py](01_pub_event.py) | Publish an event returned by an action and look up its state. |
| [02_sub_handler.py](02_sub_handler.py) | Subscribe a handler and wait for its event result. |
| [03_pub_sub_handler.py](03_pub_sub_handler.py) | Publish a second event from a subscribed handler. |
| [04_many_pub_events.py](04_many_pub_events.py) | Publish several events returned by one action. |
| [05_many_sub_handler_as_completed.py](05_many_sub_handler_as_completed.py) | Handle several event types and consume states as they complete. |
| [05_many_sub_handler_event_group.py](05_many_sub_handler_event_group.py) | Publish an event group and consume its completed states. |
| [06_pub_schedule_event.py](06_pub_schedule_event.py) | Run a cron-scheduled publisher while the bus scheduler is active. |
| [07_middleware.py](07_middleware.py) | Run middleware for one event type and inspect its handler result. |
| [08_bubus_with_injection.py](08_bubus_with_injection.py) | Use a Bubus-backed bus through a Depends provider override. |
