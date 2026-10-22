"""Action — function with typed dataclass object."""

import asyncio
from typing import assert_type

from fastsprout.actions import action
from fastsprout.core import Field, typed_dataclass


@typed_dataclass
class HeroIn:
    name: Field[str]


@typed_dataclass
class HeroOut:
    name: Field[str]


@action
async def create_hero(payload: HeroIn) -> HeroOut:
    return HeroOut(name=payload.name)


async def main() -> None:
    hero = await create_hero(HeroIn(name="Batman"))

    assert_type(hero, HeroOut)
    print("HeroOut:", hero)


if __name__ == "__main__":
    asyncio.run(main())
