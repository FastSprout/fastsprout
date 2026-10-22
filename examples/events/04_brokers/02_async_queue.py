"""Deliver local events through asyncio.Queue and wait for queued work.

AsyncQueueBroker uses the same EventBus API without calling Bubus. Supply a
queue to configure its backlog. Events are taken in queue order; their handlers
can run concurrently. Queue.join waits until delivery finishes for queued events.
"""

import asyncio
from uuid import UUID

from fastsprout.events import Event, EventBus, sub
from fastsprout.events.backend.async_queue import AsyncQueueBroker


class OrderCreated(Event):
    order_id: int


async def main() -> None:
    queue = asyncio.Queue[UUID](maxsize=16)
    broker = AsyncQueueBroker(queue)
    try:
        bus = EventBus(broker)

        @sub(OrderCreated, bus=bus)
        async def handle(event: OrderCreated) -> OrderCreated:
            return event

        state = await bus.publish(OrderCreated(order_id=42))
        await queue.join()
        done, pending = await state.wait()
        print("Handled orders:", [event.order_id for event in done])
        print("Pending handlers:", len(pending))
    finally:
        await broker.stop()


if __name__ == "__main__":
    asyncio.run(main())
