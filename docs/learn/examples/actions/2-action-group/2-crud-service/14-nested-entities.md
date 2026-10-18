# 14. Nested Entities

<!-- example-source: examples/actions/02_action_group/02_crud_service/14_nested_entities.py -->

Create and update related entities through the backend's ORM cascades.
The query explicitly loads relationships so they remain available after reading.

## Source

```python
"""Create and update related entities through the backend's ORM cascades.
The query explicitly loads relationships so they remain available after reading.
"""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Field, ReadField
from fastsprout.data import DataR, Relationship, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite://")
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Team(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    team: Field[Team] = Relationship()


heroes = DataS(Hero)


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)
        async with DataR() as datar:
            created = await heroes.create(
                Hero(name="Batman", team=Team(name="Justice League")),
                datar=datar,
            )
            query = sql.SQLQuery(
                Hero,
                statement=select(Hero)
                .where(Hero.__table__.c.id == created.id)
                .options(selectinload("*")),
            )
            found = await heroes.find_exactly_one(query, datar=datar)
            found.team.name = "Justice League International"
            updated = await heroes.update(found, datar=datar)
            print(updated.name, "belongs to", updated.team.name)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Batman belongs to Justice League International
```
