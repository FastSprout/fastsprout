from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from faststream.nats import NatsBroker as NativeNatsBroker
from testcontainers.community.nats import NatsContainer

from fastsprout.events.backend.nats import NATSBroker

from .context import broker_context

__all__ = ["TestNATS"]


def nats(
    *,
    container: NatsContainer | None = None,
    native: Callable[[str], NativeNatsBroker] = NativeNatsBroker,
    adapter: Callable[[NativeNatsBroker], NATSBroker] = NATSBroker,
    image: str = "nats:2-alpine",
) -> AbstractAsyncContextManager[NATSBroker]:
    """Own a NATS container and adapter while retaining native configuration."""
    server = container if container is not None else NatsContainer(image)
    return broker_context(
        server, lambda container: adapter(native(container.nats_uri()))
    )


TestNATS = nats
