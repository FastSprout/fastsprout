# 2. In Memory

<!-- example-source: examples/testing/03_events/02_in_memory.py -->

Test multiple subscribers with the local Bubus-backed broker.

The given fixture owns the broker, when publishes an event and waits for its
subscribers, and then checks their results. Pytest closes the broker after
the assertion, including when the test fails. No Docker server is required.

## Source

```python
"""Test multiple subscribers with the local Bubus-backed broker.

The given fixture owns the broker, when publishes an event and waits for its
subscribers, and then checks their results. Pytest closes the broker after
the assertion, including when the test fails. No Docker server is required.
"""

from collections.abc import AsyncIterator

from fastsprout.events import Event, EventBus, EventResult, sub
from fastsprout.events.backend.in_memory import InMemoryBroker
from fastsprout.testing.core import given, then, when


class OrderCreated(Event):
    order_id: int


@given("a local in-memory broker")
async def broker() -> AsyncIterator[InMemoryBroker]:
    broker = InMemoryBroker()
    try:
        yield broker
    finally:
        await broker.stop()


@when("two subscribers handle an order event")
async def handled_orders(broker: InMemoryBroker) -> EventResult[OrderCreated]:
    bus = EventBus(broker)

    @sub(OrderCreated, bus=bus)
    async def first(event: OrderCreated) -> OrderCreated:
        return event

    @sub(OrderCreated, bus=bus)
    async def second(event: OrderCreated) -> OrderCreated:
        return OrderCreated(order_id=event.order_id + 1)

    state = await bus.publish(OrderCreated(order_id=42))
    return await state.wait()


@then("both subscriber results are available")
def test_subscriber_results(handled_orders: EventResult[OrderCreated]) -> None:
    done, pending = handled_orders
    assert sorted(event.order_id for event in done) == [42, 43]
    assert pending == []
```

## Result

```text

examples/testing/03_events/02_in_memory.py::test_subscriber_results PASSED [100%]
```
