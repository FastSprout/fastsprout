"""Run the same list of Depends before a class action.
The Action base supplies dependency execution without an extra decorator.
"""

import asyncio
from typing import Annotated, assert_type

from fastsprout.actions import Action
from fastsprout.core import BaseSchema, Depends, Field, dataclass


class Hero(BaseSchema):
    name: Field[str]
    power: Field[int] = Field(default=100)


@dataclass(frozen=True)
class Actor:
    can_write: bool


async def current_actor() -> Actor:
    return Actor(can_write=True)


def check_access(actor: Annotated[Actor, Depends(current_actor)]) -> None:
    if not actor.can_write:
        raise PermissionError("Writing is forbidden")


def check_power(payload: Hero) -> None:
    if payload.power < 0:
        raise ValueError("Power must be non-negative")


class Strengthen(Action[Hero, Hero]):
    async def __call__(self, payload: Hero) -> Hero:
        return Hero(name=payload.name, power=payload.power + 1)


strengthen = Strengthen(
    dependencies=[Depends(check_access), Depends(check_power)]
)


async def main() -> None:
    hero = await strengthen(Hero(name="Batman"))
    assert_type(hero, Hero)
    print("Strengthened:", hero.name, hero.power)
    try:
        await strengthen(Hero(name="Robin", power=-1))
    except ValueError as error:
        print("Rejected:", error)


if __name__ == "__main__":
    asyncio.run(main())
