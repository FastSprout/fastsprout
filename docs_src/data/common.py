"""SQLite setup shared by the tutorial's persistence examples."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField, inject_depends
from fastsprout.data import DataR, provide_datar
from fastsprout.data.backend.sql import SQLEntity, SQLSignpost
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
store = SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


class Task(SQLEntity[int]):
    __signpost__ = store

    id: ReadField[int] = SQLField(primary_key=True)
    title: Field[str]
    completed: Field[bool] = Field(default=False)


@asynccontextmanager
async def database() -> AsyncIterator[None]:
    inject_depends.dependency_providers[DataR] = provide_datar
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)
        yield
    finally:
        await engine.dispose()
