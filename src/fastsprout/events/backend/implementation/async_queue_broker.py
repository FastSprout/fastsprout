import asyncio
from functools import partial
from uuid import UUID

from fastsprout.events.event import Eventable, EventState

from .in_memory_broker import InMemoryBroker

__all__ = ["AsyncQueueBroker"]


class AsyncQueueBroker(InMemoryBroker):
    """Schedule concurrent event delivery through a local asyncio queue."""

    def __init__(self, queue: asyncio.Queue[UUID] | None = None) -> None:
        super().__init__()
        self.queue = asyncio.Queue[UUID]() if queue is None else queue
        self.consumer: asyncio.Task[None] | None = None

    async def dispatch[E: Eventable](self, event_state: EventState[E]) -> None:
        self.prepare(event_state)
        if self.consumer is None or self.consumer.done():
            self.consumer = asyncio.create_task(self.consume())
        try:
            await self.queue.put(event_state.event.__event_id__)
        except BaseException:
            await self.retract(event_state)
            raise

    async def consume(self) -> None:
        while True:
            event_id = await self.queue.get()
            task = asyncio.create_task(self.deliver(event_id))
            self.processing[event_id] = task
            task.add_done_callback(partial(self.complete, event_id))

    def complete(self, event_id: UUID, _: asyncio.Task[None]) -> None:
        self.processing.pop(event_id, None)
        self.queue.task_done()

    async def stop(self) -> None:
        if self.consumer is not None:
            self.consumer.cancel()
            await asyncio.gather(self.consumer, return_exceptions=True)
            self.consumer = None
        await super().stop()
        while not self.queue.empty():
            self.queue.get_nowait()
            self.queue.task_done()
