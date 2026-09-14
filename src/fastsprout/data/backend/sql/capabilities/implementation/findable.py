from collections.abc import Sequence
from typing import Any, cast

from fastsprout.data.backend.sql.base import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.capabilities.protocols import Findable

__all__ = ["SQLFindable"]


class SQLFindable[E: SQLEntity[Any], Q: SQLQuery](
    Findable[E, Q], SQLDataBackend
):
    async def find_first(self, query: Q, /) -> E | None:
        async with self._get_session_factory() as session:
            return cast(
                E | None,
                (await session.execute(query._built_query.limit(1)))
                .scalars()
                .first(),
            )

    async def find_exactly_one(self, query: Q, /) -> E:
        async with self._get_session_factory() as session:
            return cast(
                E,
                (await session.execute(query._built_query.limit(2)))
                .scalars()
                .one(),
            )

    async def find_all(self, query: Q, /) -> Sequence[E]:
        async with self._get_session_factory() as session:
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
