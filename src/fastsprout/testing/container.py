from asyncio import CancelledError, create_task, shield, to_thread
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from testcontainers.core.container import DockerContainer

__all__ = ["container_context"]


@asynccontextmanager
async def container_context[C: DockerContainer](
    container: C,
) -> AsyncIterator[C]:
    """Start and stop a container off the event loop, including cancellation."""
    startup = create_task(to_thread(container.start))
    try:
        try:
            await shield(startup)
        except CancelledError:
            await startup
            raise
        yield container
    finally:
        await to_thread(container.stop)
