from collections.abc import Sequence
from typing import Any

from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.sql import Select

from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.backend.sql.streams import SQLEntityStream
from fastsprout.data.capabilities.protocols import Findable
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.streams.implementation import SimpleAsyncEntityStream

__all__ = ["SQLFindable"]


class SQLFindable[E: SQLEntity[Any]](
    Findable[E, BaseQuery[E, Select[tuple[E]]]], SQLDataBackend
):
    async def find_first(
        self, query: BaseQuery[E, Select[tuple[E]]], /
    ) -> E | None:
        return await SimpleAsyncEntityStream(
            SQLEntityStream(query, self.signpost)
        ).first()

    async def find_exactly_one(
        self, query: BaseQuery[E, Select[tuple[E]]], /
    ) -> E:
        rows = (
            await SimpleAsyncEntityStream(SQLEntityStream(query, self.signpost))
            .take(2)
            .to_list()
        )
        if not rows:
            raise NoResultFound("Query must match exactly one record")
        if len(rows) != 1:
            raise MultipleResultsFound("Query must match exactly one record")
        return rows[0]

    async def find_all(
        self, query: BaseQuery[E, Select[tuple[E]]], /
    ) -> Sequence[E]:
        return await SQLEntityStream(query, self.signpost).to_list()
