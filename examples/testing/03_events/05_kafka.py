"""Run EventBus subscribers against a disposable Kafka broker.

Run this example with Docker using pytest -m integration. Kafka uses
its native topics, consumer groups, partitions, and offsets. Pass a configured
KafkaContainer or native broker/adapter factories to customize their settings.
Results belong to this adapter's local subscribers; publishing does not wait
for handlers registered in another process.
"""

from collections.abc import AsyncIterator

import pytest

from fastsprout.events import Event, EventBus, sub
from fastsprout.events.backend.kafka import KafkaBroker
from fastsprout.testing.core import given, then, when
from fastsprout.testing.events import TestKafka


class OrderCreated(Event):
    order_id: int


@given("a Kafka adapter backed by a disposable container")
async def broker() -> AsyncIterator[KafkaBroker]:
    async with TestKafka() as broker:
        yield broker


@when("an order event is published and its subscribers finish")
async def received_orders(broker: KafkaBroker) -> list[int]:
    bus = EventBus(broker)
    received: list[int] = []

    @sub(OrderCreated, bus=bus)
    async def handle(event: OrderCreated) -> None:
        received.append(event.order_id)

    state = await bus.publish(OrderCreated(order_id=42))
    await state.wait()
    return received


@pytest.mark.integration
@then("an order event reaches the registered Kafka subscriber")
def test_delivery(received_orders: list[int]) -> None:
    assert received_orders == [42]
