from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field as SQLField
from sqlmodel import Session, create_engine

from fastsprout.core import Field, InternalField, ReadField, WriteField
from fastsprout.data.backend.sql import (
    SoftDeletableSQLEntity,
    SQLEntity,
    SQLQuery,
)
from fastsprout.data.backend.sql.capabilities import SQLAbilitable
from fastsprout.data.backend.sql.entity import SQLSignpost
from fastsprout.data.backend.sql.streams import SQLEntityStream


class SearchField[T](Field[T]): ...


class SortField[T](Field[T]): ...


class CustomSQLBase(SQLEntity[UUID], table=False):
    id: Field[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    code: SearchField[str]
    inherited: SearchField[str]


class CustomSQLMiddle(CustomSQLBase, table=False):
    sort_key: SortField[str]


class CustomSQLRecord(CustomSQLMiddle):
    name: SearchField[str]


class DefaultSQLEntity(SQLEntity[UUID], table=False):
    id: Field[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    last_login: InternalField[datetime | None] = InternalField[datetime | None](
        default=None
    )


class VisibilitySQLUser(DefaultSQLEntity):
    email: Field[str]
    password: WriteField[str]
    password_hash: InternalField[str]
    created_at: ReadField[datetime]


class Hero(SoftDeletableSQLEntity[int]):
    id: Field[int] = SQLField(primary_key=True)
    name: Field[str] = Field(default="")
    age: Field[int] = Field(default=0)


@pytest.fixture
def sql_session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine("sqlite://")
    try:
        for entity in (CustomSQLRecord, VisibilitySQLUser):
            entity.__table__.create(engine)
        yield sessionmaker(engine, class_=Session)
    finally:
        engine.dispose()


@pytest.fixture
async def sql_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Hero.__table__.create)
        async with AsyncSession(engine, expire_on_commit=False) as session:
            session.add_all(Hero(id=i, name=f"h{i}", age=i) for i in range(10))
            await session.flush()
            yield session
    finally:
        await engine.dispose()


@pytest.fixture
def sql_ability(
    sql_session: AsyncSession,
) -> SQLAbilitable[Hero, SQLQuery[Any]]:
    @asynccontextmanager
    async def shared_session() -> AsyncIterator[AsyncSession]:
        yield sql_session

    return SQLAbilitable(SQLSignpost(shared_session))


@pytest.fixture
def query() -> SQLQuery[Hero]:
    return SQLQuery(entity=Hero)


@pytest.fixture
def entity_stream(
    sql_ability: SQLAbilitable[Hero, SQLQuery[Any]], query: SQLQuery[Hero]
) -> SQLEntityStream[Hero]:
    return sql_ability.stream(query)
