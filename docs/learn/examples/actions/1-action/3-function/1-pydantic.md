# 1. Pydantic

<!-- example-source: examples/actions/01_action/03_function/01_pyd.py -->

Action — function with Pydantic objects.

## Source

```python
"""Action — function with Pydantic objects."""

import asyncio
from typing import assert_type

from fastsprout.actions import action
from fastsprout.core import BaseSchema, Field


class HeroIn(BaseSchema):
    name: Field[str]


class HeroOut(BaseSchema):
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
```

## Result

```text
HeroOut: name='Batman'
```
