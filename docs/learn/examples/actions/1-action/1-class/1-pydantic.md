# 1. Pydantic

<!-- example-source: examples/actions/01_action/01_class/01_pyd.py -->

Create a hero with a class action and a BaseSchema contract.
The class stays directly awaitable, and the result has the concrete HeroOut type.

## Source

```python
"""Create a hero with a class action and a BaseSchema contract.
The class stays directly awaitable, and the result has the concrete HeroOut type."""

import asyncio
from typing import assert_type

from fastsprout.actions import Action
from fastsprout.core import BaseSchema, Field


class HeroIn(BaseSchema):
    name: Field[str]


class HeroOut(BaseSchema):
    name: Field[str]


class CreateHero(Action[HeroIn, HeroOut]):
    async def __call__(self, payload: HeroIn) -> HeroOut:
        return HeroOut(name=payload.name)


async def main() -> None:
    hero = await CreateHero()(HeroIn(name="Batman"))

    assert_type(hero, HeroOut)
    print("HeroOut:", hero)


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
HeroOut: name='Batman'
```
