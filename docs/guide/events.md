# Publish and subscribe to events

Install the events extra:

```bash
pip install 'fastsprout[events]'
```

`EventBus` delivers events in memory. In this example, `pub` publishes the
event returned by an action, and `sub` registers a handler for that event type.
Both decorators use the same bus instance.

<!-- example-source: docs_src/events/pub_sub.py -->

```python
"""Publish an event and wait for its subscribed handler."""

import asyncio

from fastsprout.events import Event, EventBus, pub, sub

bus = EventBus()


class UserCreated(Event):
    email: str


@sub(UserCreated, bus=bus)
async def send_welcome(event: UserCreated) -> None:
    print(f"Welcome sent to {event.email}")


@pub(bus=bus)
async def register_user() -> UserCreated:
    return UserCreated(email="ada@example.com")


async def main() -> None:
    event = await register_user()
    state = await bus.get(event)
    if state is None:
        raise RuntimeError("The event was not published")
    await state.wait()


if __name__ == "__main__":
    asyncio.run(main())
```

Run the [source file](https://github.com/FastSprout/fastsprout/blob/development/docs_src/events/pub_sub.py)
from the repository root:

```bash
uv run --extra events python docs_src/events/pub_sub.py
```

## Result

```text
Welcome sent to ada@example.com
```

See the [events examples](../learn/examples/index.md) for publishers,
subscriber groups, scheduling, and middleware.

## RabbitMQ

Install `fastsprout[events-rabbit]` and pass
`RabbitMQBroker(faststream.rabbit.RabbitBroker(url))` to `EventBus`. The adapter
uses the same publishing and subscription API as the in-memory broker. Pass
`route=` or `subscription=` to configure routing and native consumers.

Event IDs survive transport. `EventState` tracks this adapter's subscriber
results and exposes failures through `result.errors`; it does not collect RPC
results from other processes. Publication waits for the native client's
acknowledgement. The default consumer acknowledges successful handlers and
rejects failed handlers. Published messages cannot be retracted. Call
`await adapter.stop()` to close an adapter used outside a testing context.

## Local brokers

`InMemoryBroker` is the default Bubus-backed adapter. `AsyncQueueBroker` schedules
events through `asyncio.Queue` without invoking Bubus. It accepts a queue instance
for backlog settings. Delivery starts in queue order and runs concurrently;
`await queue.join()` waits for delivery to finish. `await broker.stop()` cancels
unfinished work and stops the queue consumer.

- [In-memory example](../learn/examples/events/4-brokers/1-in-memory.md)
- [Async queue example](../learn/examples/events/4-brokers/2-async-queue.md)
