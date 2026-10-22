from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field as SQLField

from fastsprout.actions import DataS, Service
from fastsprout.actions.service.datas.implementation import commands, queries
from fastsprout.core import Field, InternalField, ReadDTO, ReadField, WriteDTO
from fastsprout.data import Relationship, sql

from ...common import MemoryCreate, MemoryRecord

engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
backend = sql.SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class BaseSecretEntity(sql.SQLEntity[UUID], table=False):
    __signpost__ = backend

    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]
    secret: InternalField[str]


class SecretHero(BaseSecretEntity): ...


class SecretLeague(BaseSecretEntity): ...


class SecretTeam(BaseSecretEntity):
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


class SelectedMemoryActions(Service):
    entity = MemoryRecord
    read_schema = MemoryRecord
    create_schema = MemoryCreate
    chunk_size = 2

    create = commands.create
    bulk_create = commands.bulk_create
    get = queries.get
    delete = commands.delete


class SelectedMemory(DataS[MemoryRecord]): ...
