"""Action — function with Depends - Pydantic object."""

import asyncio
from typing import assert_type

from fastsprout.actions import action
from fastsprout.core import BaseSchema, Depends, Field


class HeroIn(BaseSchema):
    name: Field[str]


class HeroPower(BaseSchema):
    value: Field[str] = Field(default="Money")


class HeroOut(BaseSchema):
    name: Field[str]
    power: HeroPower


@action
async def create_hero(
    payload: HeroIn,
    hero_power: HeroPower = Depends(),
) -> HeroOut:
    return HeroOut(name=payload.name, power=hero_power)


async def main() -> None:
    hero = await create_hero(HeroIn(name="Batman"))

    assert_type(hero, HeroOut)
    print("HeroOut:", hero)


if __name__ == "__main__":
    asyncio.run(main())
