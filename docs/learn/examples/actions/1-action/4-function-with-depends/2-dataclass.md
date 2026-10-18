# 2. Dataclass

<!-- example-source: examples/actions/01_action/04_function_with_depends/02_dataclass.py -->

Action — function with Depends - Typed dataclass object.

## Source

```python
"""Action — function with Depends - Typed dataclass object."""

import asyncio
from typing import assert_type

from fastsprout.actions import action
from fastsprout.core import Depends, Field, typed_dataclass


@typed_dataclass
class HeroIn:
    name: Field[str]


@typed_dataclass
class HeroPower:
    value: Field[str] = Field(default="Money")


@typed_dataclass
class HeroOut:
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
```

## Result

```text
HeroOut: HeroOut(name='Batman', power=HeroPower(value='Money'))
```
