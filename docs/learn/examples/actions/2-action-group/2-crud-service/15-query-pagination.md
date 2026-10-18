# 15. Query Pagination

<!-- example-source: examples/actions/02_action_group/02_crud_service/15_query_pagination.py -->

Use query conditions and pagination.
Page.total and count describe the selection before pagination.

## Source

```python
"""Use query conditions and pagination.
Page.total and count describe the selection before pagination.
"""

import asyncio
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import Field as PydanticField
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS, Page
from fastsprout.core import Field, ReadField
from fastsprout.data import DataR, sql
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Hero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    power: Field[int]


class HeroPage(Page[Hero]):
    limit: Annotated[int | None, PydanticField(ge=0, le=1000)] = 10


heroes = DataS(Hero, page=HeroPage)


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

        async with DataR() as datar:
            for name, power in (
                ("Batman", 80),
                ("Batgirl", 100),
                ("Robin", 50),
            ):
                await heroes.create(
                    heroes.create_schema(name=name, power=power), datar=datar
                )

            query = (
                datar.ability(Hero)
                .query_for(Hero)
                .where(Hero.power.gte(80))
                .order_by(Hero.power, reverse=True)
                .offset(1)
                .limit(1)
            )
            page = await heroes.list(query, datar=datar)
            print("Page:", [hero.name for hero in page.items])
            print("Pagination:", page.total, page.offset, page.limit)

            count = await heroes.count(query, datar=datar)
            print("Matching heroes:", count)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Page: ['Batman']
Pagination: 2 1 1
Matching heroes: 2
```
