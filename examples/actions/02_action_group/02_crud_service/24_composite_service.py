"""Inject a Service and its entity-specific DataS dependencies.
The injector creates GameService, HeroesService, and TeamsService within the
invocation. All operations share the explicitly supplied DataR context.
"""

import asyncio
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS, Service, action
from fastsprout.core import Depends, Field, ReadField
from fastsprout.data import DataR, sql


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
    async with database():
        async with DataR() as datar:
            await manage_game(datar)


if __name__ == "__main__":
    asyncio.run(main())
