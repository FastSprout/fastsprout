# 1. In Memory

<!-- example-source: examples/events/04_brokers/01_in_memory.py -->

Collect subscriber results from the local Bubus-backed broker.

InMemoryBroker is the default EventBus backend. It delivers events in the
current process without an external server. Waiting on the published state
collects all subscriber results.

## Source

```python
"""Collect subscriber results from the local Bubus-backed broker.

InMemoryBroker is the default EventBus backend. It delivers events in the
current process without an external server. Waiting on the published state
collects all subscriber results.
"""

import asyncio

from fastsprout.events import Event, EventBus, sub
from fastsprout.events.backend.in_memory import InMemoryBroker


class OrderCreated(Event):
    order_id: int


async def main() -> None:
    broker = InMemoryBroker()
    try:
        bus = EventBus(broker)

        @sub(OrderCreated, bus=bus)
        async def handle(event: OrderCreated) -> OrderCreated:
            return event

        state = await bus.publish(OrderCreated(order_id=42))
        done, pending = await state.wait()
        print("Handled orders:", [event.order_id for event in done])
        print("Pending handlers:", len(pending))
    finally:
        await broker.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Handled orders: [42]
Pending handlers: 0
```
