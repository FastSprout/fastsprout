from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field as SQLField
from sqlmodel import Session, create_engine

from fastsprout.core import Field, InternalField, ReadField, WriteField
from fastsprout.data.backend.sql import (
    SQLEntity,
    SQLQuery,
)
from fastsprout.data.backend.sql.capabilities import SQLAbilitable
from fastsprout.data.backend.sql.entity import SQLSignpost
from fastsprout.data.backend.sql.streams import SQLEntityStream
from fastsprout.data.capabilities.query import Gte, where
from fastsprout.testing.core import given
from fastsprout.testing.data import TestSQLite


class SearchField[T](Field[T]): ...


class SortField[T](Field[T]): ...


class CustomSQLBase(SQLEntity[UUID], table=False):
    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    code: SearchField[str]
    inherited: SearchField[str]


class CustomSQLMiddle(CustomSQLBase, table=False):
    sort_key: SortField[str]


class CustomSQLRecord(CustomSQLMiddle):
    name: SearchField[str]


class DefaultSQLEntity(SQLEntity[UUID], table=False):
    id: ReadField[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    last_login: InternalField[datetime | None] = InternalField[datetime | None](
        default=None
    )


class VisibilitySQLUser(DefaultSQLEntity):
    email: Field[str]
    password: WriteField[str]
    password_hash: InternalField[str]
    created_at: ReadField[datetime]


class Hero(SQLEntity[int]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str] = Field(default="")
    age: Field[int] = Field(default=0)


@given("a synchronous session factory for mapped field and DTO models")
def sql_session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine("sqlite://")
    try:
        for entity in (CustomSQLRecord, VisibilitySQLUser):
            entity.__table__.create(engine)
        yield sessionmaker(engine, class_=Session)
    finally:
        engine.dispose()


@given("a SQL session containing ten heroes")
async def sql_session() -> AsyncIterator[AsyncSession]:
    async with TestSQLite(Hero) as database:
        async with database.session() as session:
            session.add_all(Hero(id=i, name=f"h{i}", age=i) for i in range(10))
            await session.flush()
            yield session


@given("a signpost sharing the prepared SQL session")
def sql_signpost(
    sql_session: AsyncSession,
) -> SQLSignpost:
    @asynccontextmanager
    async def shared_session() -> AsyncIterator[AsyncSession]:
        yield sql_session

    return SQLSignpost(shared_session)


@given("SQL abilities using the shared session signpost")
def sql_ability(sql_signpost: SQLSignpost) -> SQLAbilitable[Hero]:
    return SQLAbilitable(sql_signpost)


@given("a query selecting heroes")
def query() -> SQLQuery[Hero]:
    return SQLQuery(entity=Hero)


async def matching_hero(hero: Hero) -> bool:
    return hero.age >= 5


@pytest.fixture(params=["native", "lambda", "async"])
def selected_query(request: pytest.FixtureRequest) -> SQLQuery[Hero]:
    query = SQLQuery(Hero)
    if request.param == "native":
        query.where(where(Hero.age, Gte(5)))
    elif request.param == "lambda":
        query.where(lambda hero: hero.age >= 5)
    else:
        query.where(matching_hero)
    return query.order_by(Hero.id).offset(1).limit(2)


@given("an SQL entity stream using the selected query")
def entity_stream(
    sql_ability: SQLAbilitable[Hero], query: SQLQuery[Hero]
) -> SQLEntityStream[Hero]:
    stream = sql_ability.stream(query)
    assert isinstance(stream, SQLEntityStream)
    return stream
