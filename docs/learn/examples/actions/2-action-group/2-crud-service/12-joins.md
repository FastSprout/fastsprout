# 12. Joins

<!-- example-source: examples/actions/02_action_group/02_crud_service/12_joins.py -->

Join entities selected by two queries.
Queries sharing a SQL signpost use a database join. Python predicates and
different signposts use the existing JoinedStream in the same DataR context.

## Source

```python
"""Join entities selected by two queries.
Queries sharing a SQL signpost use a database join. Python predicates and
different signposts use the existing JoinedStream in the same DataR context.
"""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS
from fastsprout.core import Field, InternalField, ReadField
from fastsprout.data import DataR, sql
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
    team_id: Field[UUID]
    secret: InternalField[str] = InternalField(default="hidden")


heroes = DataS(Hero)
teams = DataS(Team)


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)
        async with DataR() as datar:
            team = await teams.create(Team(name="Justice League"), datar=datar)
            await heroes.create(
                Hero(name="Batman", team_id=team.id), datar=datar
            )
            async for hero, team in heroes.join(
                sql.SQLQuery(Hero),
                sql.SQLQuery(Team),
                on=(Hero.team_id, Team.id),
                datar=datar,
            ):
                print(hero.name, "belongs to", team.name)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Batman belongs to Justice League
```
