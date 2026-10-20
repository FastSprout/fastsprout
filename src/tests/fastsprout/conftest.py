from collections.abc import AsyncIterator

from fastsprout.events import EventBus
from fastsprout.events.backend.in_memory import InMemoryBroker
from fastsprout.testing.core import given


@given("an in-memory broker closed after the scenario")
async def broker() -> AsyncIterator[InMemoryBroker]:
    broker = InMemoryBroker()
    try:
        yield broker
    finally:
        await broker.stop()


@given("an EventBus sharing the scenario broker")
def bus(broker: InMemoryBroker) -> EventBus:
    return EventBus(broker)
