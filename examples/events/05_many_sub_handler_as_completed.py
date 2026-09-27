"""Handle several event types and consume states as they complete."""

import asyncio

from fastsprout.events import (
    Event,
    EventBus,
    EventResult,
    EventStatesGroup,
    sub,
)

bus = EventBus()


class BaseHeroEvent(Event):
    name: str
    power: str


class HeroEventA(BaseHeroEvent):
    pass


class HeroEventB(BaseHeroEvent):
    pass


class HeroEventC(BaseHeroEvent):
    pass


class HeroEventD(BaseHeroEvent):
    pass


class HeroEventE(BaseHeroEvent):
    pass


class HeroEventF(BaseHeroEvent):
    pass


@sub(
    HeroEventA,
    HeroEventB,
    HeroEventC,
    HeroEventD,
    HeroEventE,
    HeroEventF,
    bus=bus,
)
async def sub_handler(
    e: (
        HeroEventA
        | HeroEventB
        | HeroEventC
        | HeroEventD
        | HeroEventE
        | HeroEventF
    ),
) -> None:
    print("HeroEvent type:", type(e))
    return None


async def run_example_as_completed():
    event_states_group: EventStatesGroup[
        HeroEventA, HeroEventB, HeroEventC, HeroEventD, HeroEventE, HeroEventF
    ] = await bus.publish(
        HeroEventA(name="Spider-Man", power="spider"),
        HeroEventB(name="Batman", power="money"),
        HeroEventC(name="SuperMan", power="sun"),
        HeroEventD(name="Spider-Man", power="spider"),
        HeroEventE(name="Batman", power="money"),
        HeroEventF(name="SuperMan", power="sun"),
    )
    completed = []
    async for event_state in bus.as_completed(event_states_group):
        event_result: EventResult[
            HeroEventA
            | HeroEventB
            | HeroEventC
            | HeroEventD
            | HeroEventE
            | HeroEventF
        ] = await event_state.wait()
        completed.append(type(event_result.state.event).__name__)
    print("Event Results:", sorted(completed))


async def main():
    await run_example_as_completed()


asyncio.run(main())
