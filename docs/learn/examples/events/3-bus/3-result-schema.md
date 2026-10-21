# 3. Result Schema

<!-- example-source: examples/events/03_bus/03_result_schema.py -->

Wait for a receipt from one event while retaining other subscriber results.

Passing a schema to state.wait() selects matching results. Without a schema,
wait() returns every subscriber's result. A timeout leaves pending work running.

## Source

```python
"""Wait for a receipt from one event while retaining other subscriber results.

Passing a schema to state.wait() selects matching results. Without a schema,
wait() returns every subscriber's result. A timeout leaves pending work running.
"""

import asyncio

from fastsprout.core import BaseSchema
from fastsprout.events import Event, EventBus
from fastsprout.events.backend.implementation import InMemoryBroker


class OrderCreated(Event):
    order_id: int


class Receipt(BaseSchema):
    number: str


async def issue_receipt(event: OrderCreated) -> Receipt:
    return Receipt(number=f"R-{event.order_id}")


async def audit(event: OrderCreated) -> str:
    return f"Order {event.order_id} recorded"


async def main() -> None:
    broker = InMemoryBroker()
    bus = EventBus(broker)
    bus.subscribe(OrderCreated, issue_receipt)
    bus.subscribe(OrderCreated, audit)
    try:
        state = await bus.publish(OrderCreated(order_id=42))
        receipts, _ = await state.wait(Receipt)
        for receipt in receipts:
            print(receipt.number)
        results, _ = await state.wait()
        print(f"Subscriber results: {len(results)}")
    finally:
        await broker.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
R-42
Subscriber results: 2
```
