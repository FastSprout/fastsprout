"""Action — class with Depends - Custom typed object."""

import asyncio
from typing import assert_type

from fastsprout.actions import Action, action
from fastsprout.core import Depends, Field, Schema, typed_fields


@typed_fields
class HeroIn(Schema):
    name: Field[str]

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f'HeroIn(name="{self.name}")'


@typed_fields
class HeroPower:
    value: Field[str] = Field(default="Money")

    def __repr__(self) -> str:
        return f"HeroPower(value={self.value!r})"


@typed_fields
class HeroOut(Schema):
    name: Field[str]
    power: HeroPower

    def __init__(self, name: str, power: HeroPower) -> None:
        self.name = name
        self.power = power

    def __repr__(self) -> str:
        return f"HeroOut(name={self.name!r}, power={self.power!r})"


@action
class CreateHero(Action[HeroIn, HeroOut]):
    async def __call__(
        self,
        payload: HeroIn,
        hero_power: HeroPower = Depends(),
    ) -> HeroOut:
        return HeroOut(name=payload.name, power=hero_power)


async def main() -> None:
    hero = await CreateHero()(HeroIn(name="Batman"))

    assert_type(hero, HeroOut)
    print("HeroOut:", hero)


if __name__ == "__main__":
    asyncio.run(main())
