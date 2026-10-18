# 3. Object

<!-- example-source: examples/actions/01_action/01_class/03_object.py -->

Action — class with typed custom object.

## Source

```python
"""Action — class with typed custom object."""

import asyncio
from typing import assert_type

from fastsprout.actions import Action
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
HeroOut: HeroOut(name="Batman")
```
