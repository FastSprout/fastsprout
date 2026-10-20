from asyncio import Event as Signal
from asyncio import timeout
from contextlib import AbstractAsyncContextManager

import pytest
from faststream.nats import NatsBroker as NativeNatsBroker
from testcontainers.community.nats import NatsContainer

from fastsprout.events import EventBus, EventState, sub
from fastsprout.events.backend.implementation.transport_broker import (
    TransportBroker,
)
from fastsprout.events.backend.nats import NATSBroker
from fastsprout.testing.core import then, when
from fastsprout.testing.events import TestNATS
from tests.fastsprout.events.backend.base_test_broker import (
    BaseTestBroker,
    Message,
)


@pytest.mark.integration
class TestNATSContext(BaseTestBroker):
    def make_broker(self) -> AbstractAsyncContextManager[TransportBroker]:
        return TestNATS()

    @when("one NATS adapter publishes to another adapter")
    async def remote_delivery(
        self,
    ) -> tuple[Message, Message, EventState[Message] | None]:
        container = NatsContainer("nats:2-alpine")
        received: list[Message] = []
        delivered = Signal()
        async with TestNATS(container=container) as receiver:
            bus = EventBus(receiver)

            @sub(Message, bus=bus)
            async def handler(event: Message) -> None:
                received.append(event)
                delivered.set()

            await receiver.start()
            sender = NATSBroker(NativeNatsBroker(container.nats_uri()))
            try:
                event = Message(value=7)
                async with timeout(15):
                    state = await EventBus(sender).publish(event)
                    await state.wait()
                    await delivered.wait()
                remote = await bus.get(event)
                return event, received[0], remote
            finally:
                await sender.stop()

    @then("another adapter receives the same event ID over NATS")
    def test_remote_delivery(
        self,
        remote_delivery: tuple[Message, Message, EventState[Message] | None],
    ) -> None:
        event, received, state = remote_delivery
        assert received.__event_id__ == event.__event_id__
        assert received.value == event.value
        assert state is not None
        assert state.event is received
