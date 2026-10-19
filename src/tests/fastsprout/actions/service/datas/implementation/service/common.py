from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS, Service
from fastsprout.actions.service.datas.implementation import commands, queries
from fastsprout.core import Field, InternalField, ReadDTO, ReadField, WriteDTO
from fastsprout.data import Relationship, sql

engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class SecretHero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    secret: InternalField[str]


class SecretLeague(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    secret: InternalField[str]


class SecretTeam(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    secret: InternalField[str]
    league: Field[SecretLeague | None] = Relationship()


class TeamHero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    team: Field[SecretTeam] = Relationship()


class OptionalTeamHero(sql.SQLEntity[UUID]):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    team: Field[SecretTeam | None] = Relationship()


class SecretHeroRead(ReadDTO, SecretHero): ...


class SecretHeroCreate(WriteDTO, SecretHero): ...


class SecretTeamRead(ReadDTO, SecretTeam): ...


class HeroesService(DataS[SecretHero]):
    async def strengthen(self, payload: int) -> int:
        return payload + 1


class SelectedHeroActions(Service):
    entity = SecretHero
    read_schema = SecretHeroRead
    create_schema = SecretHeroCreate
    chunk_size = 1

    create = commands.create
    get = queries.get
    delete = commands.delete
    strengthen = HeroesService.strengthen


class OptionalTeamHeroCreate(WriteDTO, OptionalTeamHero): ...
