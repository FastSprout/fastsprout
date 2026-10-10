# 1. Smart Router

<!-- example-source: examples/data/01_datar/01_smart_router.py -->

DataR - Smart data router for CRUD operations and a little more.

## Source

```python
"""DataR - Smart data router for CRUD operations and a little more."""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField
from sqlmodel import select

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLQuery
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY, SQLSignpost

engine = create_async_engine("sqlite+aiosqlite:///:memory:")


sqlite_backend = SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))

HERO_ID = uuid4()


class HeroEntity(SQLEntity[UUID]):
    __signpost__ = sqlite_backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]


FIND_HERO_WITH_ID = SQLQuery(
    entity=HeroEntity,
    statement=select(HeroEntity).where(HeroEntity.id.orm == HERO_ID),
)


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

    async with DataR() as datar:
        hero_ability = datar.ability(HeroEntity)
        await hero_ability.create(HeroEntity(id=HERO_ID, name="Batman"))
        await datar.finalize()
        found = await hero_ability.find_exactly_one(FIND_HERO_WITH_ID)
        print(found.name, found.id == HERO_ID)


asyncio.run(main())
```

## Result

```text
Batman True
```
