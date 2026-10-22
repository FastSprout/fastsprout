from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from testcontainers.core.container import DockerContainer

from fastsprout.events.backend.implementation.transport_broker import (
    TransportBroker,
)
from fastsprout.testing.container import container_context

__all__ = ["broker_context"]


@asynccontextmanager
async def broker_context[C: DockerContainer, B: TransportBroker](
    container: C, broker: Callable[[C], B]
) -> AsyncIterator[B]:
    async with container_context(container):
        adapter = broker(container)
        try:
            yield adapter
        finally:
            await adapter.stop()
