# 3. Async Queue

<!-- example-source: examples/testing/03_events/03_async_queue.py -->

Test local event delivery through an asyncio queue.

Supply a queue to the broker in given. The when step publishes an event and
waits for queue.join; then checks the subscriber result. This uses the same
typed pytest phases as the container examples, without requiring Docker.

## Source

```python
"""Test local event delivery through an asyncio queue.

Supply a queue to the broker in given. The when step publishes an event and
waits for queue.join; then checks the subscriber result. This uses the same
typed pytest phases as the container examples, without requiring Docker.
"""

from asyncio import Queue
from collections.abc import AsyncIterator
from uuid import UUID

from fastsprout.events import Event, EventBus, EventResult, sub
from fastsprout.events.backend.async_queue import AsyncQueueBroker
from fastsprout.testing.core import given, then, when


class OrderCreated(Event):
    order_id: int


@given("a local broker with a configured asyncio queue")
async def broker() -> AsyncIterator[AsyncQueueBroker]:
    broker = AsyncQueueBroker(Queue[UUID](maxsize=2))
    try:
        yield broker
    finally:
        await broker.stop()


@when("an order event finishes delivery through the queue")
async def handled_order(broker: AsyncQueueBroker) -> EventResult[OrderCreated]:
    bus = EventBus(broker)

    @sub(OrderCreated, bus=bus)
    async def handle(event: OrderCreated) -> OrderCreated:
        return event

    state = await bus.publish(OrderCreated(order_id=42))
    await broker.queue.join()
    return await state.wait()


@then("the queued order has a completed subscriber result")
def test_queue_delivery(handled_order: EventResult[OrderCreated]) -> None:
    done, pending = handled_order
    assert [event.order_id for event in done] == [42]
    assert pending == []
```

## Result

```text

examples/testing/03_events/03_async_queue.py::test_queue_delivery PASSED [100%]
```
