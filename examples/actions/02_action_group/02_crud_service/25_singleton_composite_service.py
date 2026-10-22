"""Register shared Service instances and keep using Depends().
The providers return the same GameService, HeroesService, and TeamsService
across invocations. Each invocation uses its own DataR transaction.
"""

import asyncio
from uuid import UUID, uuid4

from common import backend, database
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS, Service, action
from fastsprout.core import Depends, Field, ReadField, inject_depends
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

    def __init__(self) -> None:
        super().__init__()
        self.runs = 0


@action
async def manage_game(datar: DataR, game: GameService = Depends()) -> None:
    game.runs += 1
    print("Run:", game.runs)
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
        game = GameService()
        heroes = HeroesService()
        teams = TeamsService()
        inject_depends.dependency_providers.update(
            {
                GameService: lambda: game,
                HeroesService: lambda: heroes,
                TeamsService: lambda: teams,
            }
        )
        for _ in range(2):
            async with DataR() as datar:
                await manage_game(datar)


if __name__ == "__main__":
    asyncio.run(main())
