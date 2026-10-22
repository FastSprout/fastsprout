import os
from asyncio import Event as Signal
from asyncio import timeout
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from uuid import uuid4

import pytest
from aiokafka import AIOKafkaConsumer, TopicPartition
from aiokafka.structs import ConsumerRecord
from faststream.kafka import KafkaBroker as KafkaClient
from faststream.nats import NatsBroker as NATSClient
from faststream.rabbit import RabbitBroker as RabbitClient

from fastsprout.events import EventBus, EventState, sub
from fastsprout.events.backend.implementation.transport_broker import (
    EventMessage,
    TransportBroker,
    event_route,
)
from fastsprout.events.backend.kafka import KafkaBroker
from fastsprout.events.backend.nats import NATSBroker
from fastsprout.events.backend.rabbitmq import RabbitMQBroker
from fastsprout.events.event import Eventable
from fastsprout.testing.core import then, when
from tests.services import wait_for_service

from .base_test_broker import BaseTestBroker, Message


def unique_route() -> Callable[[type[Eventable]], str]:
    prefix = uuid4().hex

    def topic(event: type[Eventable]) -> str:
        return f"{prefix}.{event_route(event)}"

    return topic


@asynccontextmanager
async def broker_service[B: TransportBroker](broker: B) -> AsyncIterator[B]:
    try:
        await wait_for_service(broker.start)
        yield broker
    finally:
        await broker.stop()


class BaseTestBrokerService(BaseTestBroker):
    def make_service(
        self, route: Callable[[type[Eventable]], str]
    ) -> TransportBroker:
        raise NotImplementedError

    def make_broker(self) -> AbstractAsyncContextManager[TransportBroker]:
        return broker_service(self.make_service(unique_route()))

    @when("one adapter publishes to another over the service")
    async def remote_delivery(
        self,
    ) -> tuple[Message, Message, EventState[Message] | None]:
        route = unique_route()
        received: list[Message] = []
        delivered = Signal()
        async with broker_service(self.make_service(route)) as receiver:
            bus = EventBus(receiver)

            @sub(Message, bus=bus)
            async def handler(event: Message) -> None:
                received.append(event)
                delivered.set()

            await receiver.start()
            async with broker_service(self.make_service(route)) as sender:
                event = Message(value=7)
                async with timeout(30):
                    state = await EventBus(sender).publish(event)
                    await state.wait()
                    await delivered.wait()
                return event, received[0], await bus.get(event)

    @then("separate adapters preserve the event ID and payload")
    def test_remote_delivery(
        self,
        remote_delivery: tuple[Message, Message, EventState[Message] | None],
    ) -> None:
        event, received, state = remote_delivery
        assert received.__event_id__ == event.__event_id__
        assert received.value == event.value
        assert state is not None
        assert state.event is received


@pytest.mark.integration
class TestKafkaService(BaseTestBrokerService):
    def make_service(
        self, route: Callable[[type[Eventable]], str]
    ) -> KafkaBroker:
        return KafkaBroker(
            KafkaClient(os.environ["TEST_SERVICE_URL"]),
            route=route,
            group_id=f"fastsprout-{uuid4().hex}",
        )

    @when("a native Kafka consumer reads and commits a service message")
    async def native_delivery(
        self,
        broker: TransportBroker,
    ) -> tuple[Message, ConsumerRecord[bytes, bytes], int | None]:
        assert isinstance(broker, KafkaBroker)
        event = Message(value=7)
        state = await EventBus(broker).publish(event)
        await state.wait()
        consumer = AIOKafkaConsumer(
            broker.route(Message),
            bootstrap_servers=os.environ["TEST_SERVICE_URL"],
            group_id=f"native-{uuid4().hex}",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        try:
            async with timeout(30):
                await consumer.start()
                record = await consumer.getone()
                partition = TopicPartition(
                    broker.route(Message), record.partition
                )
                await consumer.commit()
                return event, record, await consumer.committed(partition)
        finally:
            await consumer.stop()

    @then("native consumers preserve Kafka keys, partitions and offsets")
    def test_native_consumer(
        self,
        native_delivery: tuple[
            Message, ConsumerRecord[bytes, bytes], int | None
        ],
    ) -> None:
        event, record, committed = native_delivery
        assert record.value is not None
        message = EventMessage.model_validate_json(record.value)
        assert message.event_id == event.__event_id__
        assert record.key == event.__event_id__.bytes
        assert committed == record.offset + 1


@pytest.mark.integration
class TestNATSService(BaseTestBrokerService):
    def make_service(
        self, route: Callable[[type[Eventable]], str]
    ) -> NATSBroker:
        return NATSBroker(
            NATSClient(os.environ["TEST_SERVICE_URL"]), route=route
        )


@pytest.mark.integration
class TestRabbitMQService(BaseTestBrokerService):
    def make_service(
        self, route: Callable[[type[Eventable]], str]
    ) -> RabbitMQBroker:
        return RabbitMQBroker(
            RabbitClient(os.environ["TEST_SERVICE_URL"]), route=route
        )
