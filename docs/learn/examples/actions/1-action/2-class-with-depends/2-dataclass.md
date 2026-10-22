# 2. Dataclass

<!-- example-source: examples/actions/01_action/02_class_with_depends/02_dataclass.py -->

Resolve a dependency in a dataclass action.
The action receives HeroPower automatically while its input and output remain typed dataclasses.

## Source

```python
"""Resolve a dependency in a dataclass action.
The action receives HeroPower automatically while its input and output remain typed dataclasses."""

import asyncio
from typing import assert_type

from fastsprout.actions import Action
from fastsprout.core import Depends, Field, Schema, typed_dataclass


@typed_dataclass
class HeroIn(Schema):
    name: Field[str]


@typed_dataclass
class HeroPower:
    value: Field[str] = Field(default="Money")


@typed_dataclass
class HeroOut(Schema):
    name: Field[str]
    power: HeroPower


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
```

## Result

```text
HeroOut: HeroOut(name='Batman', power=HeroPower(value='Money'))
```
