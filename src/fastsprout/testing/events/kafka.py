from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from faststream.kafka import KafkaBroker as NativeKafkaBroker
from testcontainers.community.kafka import KafkaContainer

from fastsprout.events.backend.kafka import KafkaBroker

from .context import broker_context

__all__ = ["TestKafka"]


def kafka(
    *,
    container: KafkaContainer | None = None,
    native: Callable[[str], NativeKafkaBroker] = NativeKafkaBroker,
    adapter: Callable[[NativeKafkaBroker], KafkaBroker] = KafkaBroker,
    image: str = "confluentinc/cp-kafka:7.6.0",
) -> AbstractAsyncContextManager[KafkaBroker]:
    """Own a Kafka container while retaining native broker and consumer options."""
    kafka_container = (
        container
        if container is not None
        else KafkaContainer(image).with_kraft()
    )
    return broker_context(
        kafka_container,
        lambda container: adapter(native(container.get_bootstrap_server())),
    )


TestKafka = kafka
