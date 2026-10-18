# 4. Custom Write Schemas

<!-- example-source: examples/actions/02_action_group/02_crud_service/04_custom_write_schemas.py -->

Override entity defaults with write schemas and keep a precise custom read DTO type.
Create, update, and patch may use different BaseSchema contracts.

## Source

```python
"""Override entity defaults with write schemas and keep a precise custom read DTO type.
Create, update, and patch may use different BaseSchema contracts.
"""

import asyncio
from typing import assert_type
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS, Page
from fastsprout.core import BaseSchema, Field, ReadDTO, ReadField
from fastsprout.core.depends import inject_depends
from fastsprout.data import DataR, provide_datar, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int] = Field(default=10)


class HeroRead(ReadDTO, Hero):
    def label(self) -> str:
        return f"{self.name}: {self.power}"


class HeroCreate(BaseSchema):
    name: Field[str]
    power: Field[int] = Field(default=20)


class HeroUpdate(BaseSchema):
    name: Field[str]
    power: Field[int]


class HeroPatch(BaseSchema):
    power: Field[int]


heroes = DataS(
    Hero,
    read=HeroRead,
    create=HeroCreate,
    update=HeroUpdate,
    patch=HeroPatch,
)


async def main() -> None:
    inject_depends.dependency_providers[DataR] = provide_datar
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

        created = await heroes.create(HeroCreate(name="Batman"))
        assert_type(created, HeroRead)
        print("Create:", created.label())

        patched = await heroes.patch(created.id, HeroPatch(power=101))
        assert_type(patched, HeroRead)
        print("Patch:", patched.label())

        updated = await heroes.update(
            created.id, HeroUpdate(name="Robin", power=50)
        )
        assert_type(updated, HeroRead)
        print("Update:", updated.label())

        page = await heroes.list()
        assert_type(page, Page[HeroRead])
        print("List:", [hero.label() for hero in page.items])
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Create: Batman: 20
Patch: Batman: 101
Update: Robin: 50
List: ['Robin: 50']
```
