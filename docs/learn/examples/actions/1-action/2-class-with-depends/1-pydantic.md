# 1. Pydantic

<!-- example-source: examples/actions/01_action/02_class_with_depends/01_pyd.py -->

Resolve a Pydantic dependency when a class action is called.
HeroPower is supplied by Depends() without becoming part of the HeroIn payload.

## Source

```python
"""Resolve a Pydantic dependency when a class action is called.
HeroPower is supplied by Depends() without becoming part of the HeroIn payload."""

import asyncio
from typing import assert_type

from fastsprout.actions import Action
from fastsprout.core import BaseSchema, Depends, Field


class HeroIn(BaseSchema):
    name: Field[str]


class HeroPower(BaseSchema):
    value: Field[str] = Field(default="Money")


class HeroOut(BaseSchema):
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
HeroOut: name='Batman' power=HeroPower(value='Money')
```
