from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import ORMExecuteState
from sqlmodel import Field as SQLField

from fastsprout.core import Field, ReadField
from fastsprout.data.backend.sql import (
    SQLEntity,
    SQLSignpost,
)
from fastsprout.data.capabilities.query import Expression
from fastsprout.testing.core import given

from .conftest import Hero


class QueryCountry(SQLEntity[int, SQLSignpost]):
    id: ReadField[int] = SQLField(primary_key=True)
    name: Field[str]


class QueryTeam(SQLEntity[int, SQLSignpost]):
    id: ReadField[int] = SQLField(primary_key=True)
    country_id: Field[int]


class BaseTestSQLJoinedQuery:
    @given("a recorder of consumed membership values")
    def consumed(self) -> list[int]:
        return []

    @given("a condition requiring lazy Python evaluation")
    def condition(self, kind: str, consumed: list[int]) -> Expression[Hero]:
        def values() -> Iterator[int]:
            consumed.extend((3, 4))
            yield from (3, 4)

        async def async_values() -> AsyncIterator[int]:
            for value in values():
                yield value

        async def matching(hero: Hero) -> bool:
            return hero.age in (3, 4)

        conditions: dict[str, Expression[Hero]] = {
            "native": Hero.age.in_([3, 4]),
            "sync": Hero.age.in_(values()),
            "async": Hero.age.in_(async_values()),
            "python": lambda hero: hero.age in (3, 4),
            "async-python": matching,
        }
        return conditions[kind]

    @given("three SQL entities sharing the prepared session and signpost")
    async def joined_source(
        self,
        sql_session: AsyncSession,
        sql_signpost: SQLSignpost,
        monkeypatch: pytest.MonkeyPatch,
    ) -> SQLSignpost:
        for entity in (Hero, QueryTeam, QueryCountry):
            monkeypatch.setattr(
                entity, "__signpost__", sql_signpost, raising=False
            )
        for entity in (QueryTeam, QueryCountry):
            await sql_session.run_sync(
                lambda session, table=entity.__table__: table.create(
                    session.connection()
                )
            )
        sql_session.add_all(
            [
                QueryTeam(id=3, country_id=1),
                QueryTeam(id=4, country_id=1),
                QueryCountry(id=1, name="Poland"),
            ]
        )
        await sql_session.flush()
        return sql_signpost

    @given("a recorder of executed SELECT statements")
    def selects(
        self, joined_source: SQLSignpost, sql_session: AsyncSession
    ) -> Iterator[list[str]]:
        statements: list[str] = []

        def record(state: ORMExecuteState) -> None:
            if state.is_select:
                statements.append(str(state.statement))

        event.listen(sql_session.sync_session, "do_orm_execute", record)
        try:
            yield statements
        finally:
            event.remove(sql_session.sync_session, "do_orm_execute", record)
