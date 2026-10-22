from contextlib import AbstractAsyncContextManager
from types import ModuleType
from typing import Self

import pytest
from faststream.kafka import KafkaBroker as KafkaClient
from faststream.nats import NatsBroker as NATSClient
from faststream.rabbit import RabbitBroker as RabbitClient
from testcontainers.community.kafka import KafkaContainer
from testcontainers.community.nats import NatsContainer
from testcontainers.community.rabbitmq import RabbitMqContainer

import fastsprout.testing.events.kafka as kafka_context
import fastsprout.testing.events.nats as nats_context
import fastsprout.testing.events.rabbitmq as rabbitmq_context
from fastsprout.events.backend.implementation.transport_broker import (
    TransportBroker,
)
from fastsprout.events.backend.kafka import KafkaBroker
from fastsprout.events.backend.nats import NATSBroker
from fastsprout.events.backend.rabbitmq import RabbitMQBroker
from fastsprout.testing.core import given, then, when
from fastsprout.testing.events import TestKafka, TestNATS, TestRabbitMQ

from ..common import RecordedContainer


class KafkaServer(RecordedContainer, KafkaContainer):
    def start(self, timeout: int = 30) -> Self:
        return super().start()

    def get_bootstrap_server(self) -> str:
        return "localhost:19092"


class NATSServer(RecordedContainer, NatsContainer):
    def nats_uri(self) -> str:
        return "nats://localhost:14222"


class RabbitServer(RecordedContainer, RabbitMqContainer):
    port = 5672
    username = "tester"
    password = "secret"
    vhost = "testing"

    def get_container_host_ip(self) -> str:
        return "localhost"

    def get_exposed_port(self, port: int) -> int:
        return port + 10000


class BaseTestBrokerFactory[C: RecordedContainer, B: TransportBroker]:
    server_type: type[C]
    broker_type: type[B]
    expected_url: str
    context_module: ModuleType
    container_name: str
    image: str

    def make_broker(
        self, server: C | None, urls: list[str]
    ) -> AbstractAsyncContextManager[B]:
        raise NotImplementedError

    @given("a broker container recording startup and cleanup without Docker")
    def server(self, monkeypatch: pytest.MonkeyPatch, images: list[str]) -> C:
        server = self.server_type()

        def construct(image: str) -> C:
            images.append(image)
            server.image = image
            return server

        monkeypatch.setattr(self.context_module, self.container_name, construct)
        return server

    @given("a recorder of images used when no container is supplied")
    def images(self) -> list[str]:
        return []

    @given("a recorder of addresses passed to the native broker factory")
    def urls(self) -> list[str]:
        return []

    @given("a recorder of adapters stopped by the context")
    def stopped(self) -> list[B]:
        return []

    @when("a configured testing broker context is entered and exited")
    async def configured(
        self,
        server: C,
        urls: list[str],
        custom: bool,
        stopped: list[B],
        monkeypatch: pytest.MonkeyPatch,
    ) -> B:
        async with self.make_broker(server if custom else None, urls) as broker:
            original_stop = broker.stop

            async def stop() -> None:
                await original_stop()
                stopped.append(broker)

            monkeypatch.setattr(broker, "stop", stop)
            return broker

    @pytest.mark.parametrize("custom", [False, True])
    @then(
        "the native factory receives the address and the container is released"
    )
    def test_configuration(
        self,
        server: C,
        urls: list[str],
        configured: B,
        images: list[str],
        custom: bool,
        stopped: list[B],
    ) -> None:
        assert type(configured) is self.broker_type
        assert urls == [self.expected_url]
        assert server.calls == ["start", "stop"]
        assert images == ([] if custom else [self.image])
        assert stopped == [configured]


class TestKafkaFactory(BaseTestBrokerFactory[KafkaServer, KafkaBroker]):
    server_type = KafkaServer
    broker_type = KafkaBroker
    expected_url = "localhost:19092"
    context_module = kafka_context
    container_name = "KafkaContainer"
    image = "confluentinc/cp-kafka:7.7.0"

    def make_broker(
        self, server: KafkaServer | None, urls: list[str]
    ) -> AbstractAsyncContextManager[KafkaBroker]:
        def native(url: str) -> KafkaClient:
            urls.append(url)
            return KafkaClient(url, client_id="factory-test")

        return TestKafka(container=server, native=native, image=self.image)


class TestNATSFactory(BaseTestBrokerFactory[NATSServer, NATSBroker]):
    server_type = NATSServer
    broker_type = NATSBroker
    expected_url = "nats://localhost:14222"
    context_module = nats_context
    container_name = "NatsContainer"
    image = "nats:2.10-alpine"

    def make_broker(
        self, server: NATSServer | None, urls: list[str]
    ) -> AbstractAsyncContextManager[NATSBroker]:
        def native(url: str) -> NATSClient:
            urls.append(url)
            return NATSClient(url, name="factory-test")

        return TestNATS(container=server, native=native, image=self.image)


class TestRabbitMQFactory(BaseTestBrokerFactory[RabbitServer, RabbitMQBroker]):
    server_type = RabbitServer
    broker_type = RabbitMQBroker
    expected_url = "amqp://tester:secret@localhost:15672/testing"
    context_module = rabbitmq_context
    container_name = "RabbitMqContainer"
    image = "rabbitmq:4.0-alpine"

    def make_broker(
        self, server: RabbitServer | None, urls: list[str]
    ) -> AbstractAsyncContextManager[RabbitMQBroker]:
        def native(url: str) -> RabbitClient:
            urls.append(url)
            return RabbitClient(url, app_id="factory-test")

        return TestRabbitMQ(container=server, native=native, image=self.image)
