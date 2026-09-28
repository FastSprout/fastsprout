from collections.abc import Sequence
from typing import Any, cast

from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import Findable

__all__ = ["SQLFindable"]


class SQLFindable[E: SQLEntity[Any], Q: SQLQuery](
    Findable[E, Q], SQLDataBackend
):
    async def find_first(self, query: SQLQuery[E], /) -> E | None:
        async with self.session() as session:
            return cast(
                E | None,
                (await session.execute(query._built_query.limit(1)))
                .scalars()
                .first(),
            )

    async def find_exactly_one(self, query: SQLQuery[E], /) -> E:
        async with self.session() as session:
            return cast(
                E,
                (await session.execute(query._built_query.limit(2)))
                .scalars()
                .one(),
            )

    async def find_all(self, query: SQLQuery[E], /) -> Sequence[E]:
        async with self.session() as session:
            return cast(
                Sequence[E],
                (
                    await session.execute(
                        query._built_query,
                    )
                )
                .scalars()
                .all(),
            )
