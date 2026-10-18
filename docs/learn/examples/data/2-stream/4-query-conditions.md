# 4. Query Conditions

<!-- example-source: examples/data/02_stream/04_query_conditions.py -->

Build field conditions once and reuse them in Query and stream.filter.

Query exposes And, Or, Xor, and Nand. Field methods check their value types.
An iterator passed to in_ is read on first evaluation and cached for reuse;
it must be finite, and its values occupy memory until the condition is freed.

## Source

```python
"""Build field conditions once and reuse them in Query and stream.filter.

Query exposes And, Or, Xor, and Nand. Field methods check their value types.
An iterator passed to in_ is read on first evaluation and cached for reuse;
it must be finite, and its values occupy memory until the condition is freed.
"""

import asyncio
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity, SQLQuery, SQLSignpost


class Hero(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]
    power: Field[int]
    active: Field[bool]


async def selected_powers() -> AsyncIterator[int]:
    yield 10
    yield 20


async def main() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    Hero.__signpost__ = SQLSignpost(factory)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Hero.__table__.create)
        async with factory() as session:
            session.add_all(
                [
                    Hero(id=1, name="Batman", power=80, active=True),
                    Hero(id=2, name="Robin", power=20, active=False),
                    Hero(id=3, name="Batgirl", power=60, active=True),
                ]
            )
            await session.commit()

        selected = Hero.power.in_(selected_powers())
        query = SQLQuery(Hero)
        query.where(
            query.Or(
                Hero.name.eq("Batman"),
                Hero.power.gte(50),
                selected,
                Hero.power.between(50, 50),
            ),
            lambda hero: hero.active,
        ).order_by(Hero.id)

        async with DataR() as data:
            found = await data.stream(query).to_list()
            reused = (
                await data.stream(SQLQuery(Hero)).filter(selected).to_list()
            )
            exclusive = await data.stream(
                SQLQuery(Hero).where(
                    query.Xor(Hero.name.eq("Batman"), Hero.power.gte(50))
                )
            ).to_list()
            print("Query:", [hero.name for hero in found])
            print("Reused condition:", [hero.name for hero in reused])
            print("Exclusive condition:", [hero.name for hero in exclusive])
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Query: ['Batman', 'Batgirl']
Reused condition: ['Robin']
Exclusive condition: ['Batgirl']
```
