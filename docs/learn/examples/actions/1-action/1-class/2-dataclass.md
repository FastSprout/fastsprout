# 2. Dataclass

<!-- example-source: examples/actions/01_action/01_class/02_dataclass.py -->

Create a hero with a class action and typed dataclasses.
The same action API works without Pydantic models.

## Source

```python
"""Create a hero with a class action and typed dataclasses.
The same action API works without Pydantic models."""

import asyncio
from typing import assert_type

from fastsprout.actions import Action
from fastsprout.core import Field, typed_dataclass


@typed_dataclass
class HeroIn:
    name: Field[str]


@typed_dataclass
class HeroOut:
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
HeroOut: HeroOut(name='Batman')
```
