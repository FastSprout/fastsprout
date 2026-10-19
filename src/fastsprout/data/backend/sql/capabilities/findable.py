from collections.abc import Sequence
from typing import Any

from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity, SQLSource
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.backend.sql.streams import SQLEntityStream
from fastsprout.data.capabilities.protocols import Findable
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream

__all__ = ["SQLFindable"]


class SQLFindable[E: SQLEntity[Any]](Findable[E, SQLQuery[E]], SQLDataBackend):
    async def find_first[S: SQLSource](
        self, query: SQLQuery[E, S], /
    ) -> E | None:
        return await SimpleAsyncEntityStream(
            SQLEntityStream(query, self._signpost)
        ).first()

    async def find_exactly_one[S: SQLSource](
        self, query: SQLQuery[E, S], /
    ) -> E:
        rows = (
            await SimpleAsyncEntityStream(
                SQLEntityStream(query, self._signpost)
            )
            .take(2)
            .to_list()
        )
        if not rows:
            raise NoResultFound("Query must match exactly one record")
        if len(rows) != 1:
            raise MultipleResultsFound("Query must match exactly one record")
        return rows[0]

    async def find_all[S: SQLSource](
        self, query: SQLQuery[E, S], /
    ) -> Sequence[E]:
        return await SQLEntityStream(query, self._signpost).to_list()
