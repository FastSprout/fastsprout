"""Publish several events returned by one action."""

import asyncio
from collections.abc import Sequence

from fastsprout.events import Event, EventBus, pub
from fastsprout.events.event import EventStatesGroup

bus = EventBus()


class HeroEvent(Event):
    name: str
    power: str


@pub(bus=bus)
async def pub_event() -> list[HeroEvent]:
    return [
        HeroEvent(name="Spider-Man", power="spider"),
        HeroEvent(name="Batman", power="money"),
        HeroEvent(name="SuperMan", power="sun"),
    ]


async def main():
    e: Sequence[HeroEvent] = await pub_event()

    event_states: EventStatesGroup[*tuple[HeroEvent, ...]] = await bus.get(*e)

    print("Event States:", event_states)


asyncio.run(main())
