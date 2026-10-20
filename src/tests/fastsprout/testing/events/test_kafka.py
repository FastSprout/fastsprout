from asyncio import timeout
from contextlib import AbstractAsyncContextManager

import pytest
from aiokafka import AIOKafkaConsumer, TopicPartition
from aiokafka.structs import ConsumerRecord
from testcontainers.community.kafka import KafkaContainer

from fastsprout.events import EventBus
from fastsprout.events.backend.implementation.transport_broker import (
    EventMessage,
    TransportBroker,
    event_route,
)
from fastsprout.testing.core import then, when
from fastsprout.testing.events.kafka import TestKafka
from tests.fastsprout.events.backend.base_test_broker import (
    BaseTestBroker,
    Message,
)


@pytest.mark.integration
class TestKafkaContext(BaseTestBroker):
    def make_broker(self) -> AbstractAsyncContextManager[TransportBroker]:
        return TestKafka()

    @when("a native Kafka consumer reads and commits a published message")
    async def native_delivery(
        self,
    ) -> tuple[Message, ConsumerRecord[bytes, bytes], int | None]:
        container = KafkaContainer("confluentinc/cp-kafka:7.6.0").with_kraft()
        event = Message(value=7)
        topic = event_route(Message)
        async with TestKafka(container=container) as broker:
            state = await EventBus(broker).publish(event)
            await state.wait()
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=container.get_bootstrap_server(),
                group_id="native-probe",
                auto_offset_reset="earliest",
                enable_auto_commit=False,
            )
            try:
                async with timeout(20):
                    await consumer.start()
                    record = await consumer.getone()
                    partition = TopicPartition(topic, record.partition)
                    await consumer.commit()
                    return event, record, await consumer.committed(partition)
            finally:
                await consumer.stop()

    @then("native Kafka consumers retain keys, partitions, groups, and offsets")
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
