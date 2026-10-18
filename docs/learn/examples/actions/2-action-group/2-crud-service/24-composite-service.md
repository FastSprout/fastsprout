# 24. Composite Service

<!-- example-source: examples/actions/02_action_group/02_crud_service/24_composite_service.py -->

Inject a Service and its entity-specific DataS dependencies.
The injector creates GameService, HeroesService, and TeamsService within the
invocation. All operations share the explicitly supplied DataR context.

## Source

```python
"""Inject a Service and its entity-specific DataS dependencies.
The injector creates GameService, HeroesService, and TeamsService within the
invocation. All operations share the explicitly supplied DataR context.
"""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS, Service, action
from fastsprout.core import Depends, Field, ReadField
from fastsprout.data import DataR, sql

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


class HeroesService(DataS[Hero]): ...


class TeamsService(DataS[Team]): ...


class GameService(Service):
    heroes: HeroesService = Depends()
    teams: TeamsService = Depends()


@action
async def manage_game(datar: DataR, game: GameService = Depends()) -> None:
    team = await game.teams.create(Team(name="Justice League"), datar=datar)
    hero = await game.heroes.create(
        Hero(name="Batman", team_id=team.id), datar=datar
    )
    print("Team:", team.name)
    print("Hero:", hero.name)
    print("Same team:", hero.team_id == team.id)

    await game.heroes.delete(hero.id, datar=datar)
    print("Heroes:", await game.heroes.count(datar=datar))
    print("Teams:", await game.teams.count(datar=datar))


async def main() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Team.__table__.create)
            await connection.run_sync(Hero.__table__.create)
        async with DataR() as datar:
            await manage_game(datar)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

## Result

```text
Team: Justice League
Hero: Batman
Same team: True
Heroes: 0
Teams: 1
```
