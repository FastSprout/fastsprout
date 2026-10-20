# EVENTS Examples

The events layer publishes events through EventBus, delivers them
to subscribers, tracks results, and runs scheduled publishers and middleware.
Run from the repository root with the events extra:

```bash
uv run --extra events python examples/events/01_decorators/01_pub_pusher.py
```

## 1. Decorators

| File | Shows |
| --- | --- |
| [01_decorators/01_pub_pusher.py](01_decorators/01_pub_pusher.py) | Publish an event returned by an action and look up its state. |
| [01_decorators/02_sub_handler.py](01_decorators/02_sub_handler.py) | Subscribe a handler and wait for its event result. |
| [01_decorators/03_pub_sub_handler.py](01_decorators/03_pub_sub_handler.py) | Publish a second event from a subscribed handler. |

## 2. Advance Decorators

| File | Shows |
| --- | --- |
| [02_advance_decorators/01_events_group/01_as_completed.py](02_advance_decorators/01_events_group/01_as_completed.py) | Handle several event types and consume states as they complete. |
| [02_advance_decorators/01_events_group/02_simple_list.py](02_advance_decorators/01_events_group/02_simple_list.py) | Publish several events returned by one action. |
| [02_advance_decorators/01_events_group/03_event_group_in_bus.py](02_advance_decorators/01_events_group/03_event_group_in_bus.py) | Publish an event group and consume its completed states. |
| [02_advance_decorators/01_schedule_event.py](02_advance_decorators/01_schedule_event.py) | Run a cron-scheduled publisher while the bus scheduler is active. |

## 3. Bus

| File | Shows |
| --- | --- |
| [03_bus/01_middleware.py](03_bus/01_middleware.py) | Run middleware for one event type and inspect its handler result. |
| [03_bus/02_custom_event_bus.py](03_bus/02_custom_event_bus.py) | Use a Bubus-backed bus through a Depends provider override. |

## 4. Brokers

| File | Shows |
| --- | --- |
| [04_brokers/01_in_memory.py](04_brokers/01_in_memory.py) | Collect subscriber results from the local Bubus-backed broker. |
| [04_brokers/02_async_queue.py](04_brokers/02_async_queue.py) | Deliver local events through asyncio.Queue and wait for queued work. |
