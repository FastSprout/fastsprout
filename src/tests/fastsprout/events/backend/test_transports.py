from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from uuid import uuid4

import pytest
from faststream.kafka import KafkaBroker as KafkaClient
from faststream.kafka import TestKafkaBroker as KafkaHarness
from faststream.nats import NatsBroker as NATSClient
from faststream.nats import TestNatsBroker as NATSHarness
from faststream.rabbit import RabbitBroker as RabbitClient
from faststream.rabbit import TestRabbitBroker as RabbitHarness

from fastsprout.core import BaseSchema
from fastsprout.events import Event, EventResult, EventState
from fastsprout.events.backend.implementation.transport_broker import (
    EventMessage,
    TransportBroker,
)
from fastsprout.events.backend.kafka import KafkaBroker
from fastsprout.events.backend.nats import NATSBroker
from fastsprout.events.backend.rabbitmq import RabbitMQBroker
from fastsprout.testing.core import given, then, when


class Notification(Event):
    text: str


class Message(Notification): ...


class Reply(BaseSchema):
    text: str


class BaseTestTransport:
    def make_broker(self) -> AbstractAsyncContextManager[TransportBroker]:
        raise NotImplementedError

    @given("a transport adapter using the SDK's in-process test broker")
    async def broker(self) -> AsyncIterator[TransportBroker]:
        async with self.make_broker() as broker:
            yield broker

    @given("a recorder of event IDs received by the subscriber")
    def received(self) -> list[Message]:
        return []

    @when("a transported message reaches a successful or failing subscriber")
    async def delivered(
        self, broker: TransportBroker, received: list[Message], fail: bool
    ) -> tuple[EventResult[Message, Reply], ValueError | None]:
        async def handler(event: Message) -> Reply:
            received.append(event)
            if fail:
                raise ValueError("Rejected")
            return Reply(text=event.text.upper())

        async def ignore(event: Event) -> None:
            pass

        broker.subscribe(Message, handler)
        broker.subscribe(Message, handler)
        broker.subscribe(Notification, ignore)
        broker.subscribe(Event, ignore)
        event = Message(text="hello")
        state = EventState(event)
        error: ValueError | None = None
        try:
            await broker.dispatch(state)
        except ValueError as rejected:
            error = rejected
        return await state.wait(), error

    @pytest.mark.parametrize("fail", [False, True])
    @then(
        "transport delivery preserves results and propagates subscriber failures"
    )
    def test_delivery(
        self,
        delivered: tuple[EventResult[Message, Reply], ValueError | None],
        received: list[Message],
        fail: bool,
    ) -> None:
        result, error = delivered
        successful, pending = result
        assert len(received) == 2
        assert all(
            event.__event_id__ == result.state.event.__event_id__
            for event in received
        )
        assert pending == []
        if fail:
            assert isinstance(error, ValueError)
        else:
            assert error is None
            assert [reply.text for reply in successful] == ["HELLO", "HELLO"]

    @when("an adapter uses a caller-provided subscriber factory")
    async def custom_subscription(self, broker: TransportBroker) -> list[str]:
        if not isinstance(broker, KafkaBroker | NATSBroker | RabbitMQBroker):
            raise TypeError("Expected a FastStream adapter")
        calls: list[str] = []

        async def handler(message: EventMessage) -> None:
            calls.append(message.payload)

        def subscribe(
            event_type: type[Event],
            receive: Callable[[EventMessage], Awaitable[None]],
        ) -> Callable[[], Awaitable[None]]:
            calls.append(event_type.__name__)

            async def start() -> None:
                await receive(
                    EventMessage(event_id=uuid4(), payload="configured")
                )

            return start

        broker.subscription = subscribe
        await broker.register(Message, handler)()
        return calls

    @then("the subscriber factory receives the event type and handler")
    def test_custom_subscription(self, custom_subscription: list[str]) -> None:
        assert custom_subscription == ["Message", "configured"]

    @when("the transport receives an event published outside this broker")
    async def external_delivery(
        self, broker: TransportBroker, received: list[Message]
    ) -> tuple[EventResult[Message, Reply], bool]:
        async def handler(event: Message) -> Reply:
            received.append(event)
            return Reply(text=event.text.upper())

        broker.subscribe(Message, handler)
        await broker.start()
        event = Message(text="external")
        await broker.send(
            EventMessage(
                event_id=event.__event_id__, payload=event.model_dump_json()
            ),
            Message,
        )
        state = await broker.get(event)
        if state is None:
            raise LookupError("Transport did not register the received event")
        return await state.wait(Reply), await broker.retract(state)

    @then("external events acquire local state and cannot be retracted")
    def test_external_delivery(
        self,
        external_delivery: tuple[EventResult[Message, Reply], bool],
        received: list[Message],
    ) -> None:
        result, retracted = external_delivery
        successful, pending = result
        assert successful == [Reply(text="EXTERNAL")]
        assert pending == []
        assert [event.__event_id__ for event in received] == [
            result.state.event.__event_id__
        ]
        assert not retracted


class TestKafka(BaseTestTransport):
    @asynccontextmanager
    async def make_broker(self) -> AsyncIterator[KafkaBroker]:
        native = KafkaClient()
        async with KafkaHarness(native, connect_only=False):
            broker = KafkaBroker(native)
            try:
                yield broker
            finally:
                await broker.stop()


class TestNATS(BaseTestTransport):
    @asynccontextmanager
    async def make_broker(self) -> AsyncIterator[NATSBroker]:
        native = NATSClient()
        async with NATSHarness(native, connect_only=False):
            broker = NATSBroker(native)
            try:
                yield broker
            finally:
                await broker.stop()


class TestRabbitMQ(BaseTestTransport):
    @asynccontextmanager
    async def make_broker(self) -> AsyncIterator[RabbitMQBroker]:
        native = RabbitClient()
        async with RabbitHarness(native, connect_only=False):
            broker = RabbitMQBroker(native)
            try:
                yield broker
            finally:
                await broker.stop()
