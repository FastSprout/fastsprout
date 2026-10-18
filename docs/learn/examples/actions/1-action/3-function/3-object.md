# 3. Object

<!-- example-source: examples/actions/01_action/03_function/03_object.py -->

Action — function with typed custom object.

## Source

```python
"""Action — function with typed custom object."""

import asyncio
from typing import assert_type

from fastsprout.actions import action
from fastsprout.core import Field, typed_fields


@typed_fields
class HeroIn:
    name: Field[str]

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f'HeroIn(name="{self.name}")'


@typed_fields
class HeroOut:
    name: Field[str]

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f'HeroOut(name="{self.name}")'


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
HeroOut: HeroOut(name="Batman")
```
