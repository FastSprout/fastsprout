"""Use a Bubus-backed bus through a Depends provider override."""

import asyncio

from bubus import EventBus as NativeBubusBus

from fastsprout.core import inject_depends
from fastsprout.events import Event, EventBus, pub, sub
from fastsprout.events.backend.implementation import InMemoryBroker


class Greeting(Event):
    name: str


native_bus = NativeBubusBus()
bus = EventBus(InMemoryBroker(native_bus))
inject_depends.dependency_overrides[EventBus] = lambda: bus


@sub(Greeting)
async def greet(event: Greeting) -> None:
    print(f"Hello, {event.name}!")


@pub()
async def make_greeting() -> Greeting:
    return Greeting(name="FastSprout")


async def main() -> None:
    try:
        event = await make_greeting()
        state = await bus.get(event)
        assert state is not None
        await state.wait()
    finally:
        del inject_depends.dependency_overrides[EventBus]


asyncio.run(main())
