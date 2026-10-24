"""SQLite setup shared by the runnable DataS examples."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from fastsprout.core import inject_depends
from fastsprout.data import DataR, provide_datar
from fastsprout.data.backend.sql import SQLSignpost
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY

__all__ = ["backend", "database"]

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
backend = SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))


@asynccontextmanager
async def database() -> AsyncIterator[None]:
    inject_depends.dependency_providers[DataR] = provide_datar
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)
        yield
    finally:
        await engine.dispose()
