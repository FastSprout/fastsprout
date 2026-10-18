# 16. Reusable Query

<!-- example-source: examples/actions/02_action_group/02_crud_service/16_reusable_query.py -->

Build a reusable query with field conditions, a lambda, and an async predicate.
The same query serves both list and count.

## Source

```python
"""Build a reusable query with field conditions, a lambda, and an async predicate.
The same query serves both list and count.
"""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
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


def hero_query(minimum_power: int, name_prefix: str) -> sql.SQLQuery[Hero]:
    return sql.SQLQuery(Hero).where(
        Hero.power.gte(minimum_power),
        lambda hero: hero.name.startswith(name_prefix),
    )


async def has_power(hero: Hero) -> bool:
    return hero.power > 0


class HeroesService(DataS[Hero]): ...


heroes = HeroesService()


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

            query = hero_query(minimum_power=90, name_prefix="Bat").where(
                has_power
            )
            page = await heroes.list(query, datar=datar)
            count = await heroes.count(query, datar=datar)

            print("Selected heroes:", [hero.name for hero in page.items])
            print("Matching heroes:", count)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Selected heroes: ['Batgirl']
Matching heroes: 1
```
