from collections.abc import AsyncIterator

from .datar import DataR

__all__ = ["provide_datar"]


async def provide_datar() -> AsyncIterator[DataR]:
    """Provide a transactional DataR when explicitly registered with DI."""
    async with DataR() as datar:
        yield datar
