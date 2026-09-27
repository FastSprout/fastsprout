"""Publish a typed CreateEvent when DataR persists an entity."""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.core import Field
from fastsprout.data import DataR
from fastsprout.data.backend.sql import SQLEntity
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY, SQLSignpost
from fastsprout.data.events import CreateEvent
from fastsprout.events import EventBus, sub

engine = create_async_engine("sqlite+aiosqlite:///:memory:")


sqlite_backend = SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))
bus = EventBus()

HERO_ID = uuid4()


class HeroEntity(SQLEntity[UUID]):
    __signpost__ = sqlite_backend

    id: Field[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: Field[str]


@sub(CreateEvent[HeroEntity], bus=bus)
async def listen_creating_hero(e: CreateEvent[HeroEntity]):
    print("Create Event:", e.entity.name)


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)

    async with DataR(bus=bus) as datar:
        hero_ability = datar.ability(HeroEntity)
        await hero_ability.create(HeroEntity(id=HERO_ID, name="Batman"))

    states = await bus.get(CreateEvent[HeroEntity])
    await (await anext(states)).wait()


asyncio.run(main())
