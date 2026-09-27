"""Run a cron-scheduled publisher while the bus scheduler is active."""

import asyncio
from collections.abc import AsyncIterator

from fastsprout.events import EventBus, ScheduleEvent, pub, sub
from fastsprout.events.event import EventState

bus = EventBus()


class HeroEvent(ScheduleEvent):
    name: str
    power: str


@pub(bus=bus, on="* * * * * *")
async def pub_hero_event() -> HeroEvent:
    return HeroEvent(name="Spider-Man", power="spider")


@sub(HeroEvent, bus=bus)
async def sub_hero_event(e: HeroEvent) -> None:
    print("HeroEvent:", e)
    return None


async def main() -> None:
    async with bus.scheduler():
        await asyncio.sleep(1.2)
        event_state: AsyncIterator[EventState[HeroEvent]] = await bus.get(
            HeroEvent
        )
        print("Event Result:", await (await anext(event_state)).wait())


asyncio.run(main())
