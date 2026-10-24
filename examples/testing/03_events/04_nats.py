"""Deliver an EventBus event through a disposable NATS broker.

Run this example with Docker using pytest -m integration. Register
handlers before publishing; the adapter connects and starts consumers on
first dispatch. The context closes the adapter and removes the container.
EventState tracks results from this adapter's subscribers, not remote RPC
results. A published transport message cannot be retracted.
"""

from collections.abc import AsyncIterator

import pytest

from fastsprout.events import Event, EventBus, sub
from fastsprout.events.backend.nats import NATSBroker
from fastsprout.testing.core import given, then, when
from fastsprout.testing.events import TestNATS


class OrderCreated(Event):
    order_id: int


@given("a NATS adapter backed by a disposable container")
async def broker() -> AsyncIterator[NATSBroker]:
    async with TestNATS() as broker:
        yield broker


@when("an order event is published and its subscribers finish")
async def received_orders(broker: NATSBroker) -> list[int]:
    bus = EventBus(broker)
    received: list[int] = []

    @sub(OrderCreated, bus=bus)
    async def handle(event: OrderCreated) -> None:
        received.append(event.order_id)

    state = await bus.publish(OrderCreated(order_id=42))
    await state.wait()
    return received


@pytest.mark.integration
@then("an order event reaches the registered handler")
def test_delivery(received_orders: list[int]) -> None:
    assert received_orders == [42]
