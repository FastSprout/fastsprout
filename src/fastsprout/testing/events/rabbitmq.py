from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from aio_pika.connection import make_url
from faststream.rabbit import RabbitBroker
from testcontainers.community.rabbitmq import RabbitMqContainer

from fastsprout.events.backend.rabbitmq import RabbitMQBroker

from .context import broker_context

__all__ = ["TestRabbitMQ", "rabbit_url"]


def rabbitmq(
    *,
    container: RabbitMqContainer | None = None,
    native: Callable[[str], RabbitBroker] = RabbitBroker,
    adapter: Callable[[RabbitBroker], RabbitMQBroker] = RabbitMQBroker,
    image: str = "rabbitmq:4.1.0-alpine",
) -> AbstractAsyncContextManager[RabbitMQBroker]:
    """Own a RabbitMQ container and adapter, preserving native configuration."""
    rabbit = container if container is not None else RabbitMqContainer(image)

    return broker_context(
        rabbit, lambda container: adapter(native(rabbit_url(container)))
    )


def rabbit_url(container: RabbitMqContainer) -> str:
    return str(
        make_url(
            host=container.get_container_host_ip(),
            port=int(container.get_exposed_port(container.port)),
            login=container.username,
            password=container.password,
            virtualhost=container.vhost,
        )
    )


TestRabbitMQ = rabbitmq
