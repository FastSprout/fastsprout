from dataclasses import dataclass
from typing import Any

from sqlalchemy import delete, insert, select, update
from sqlalchemy.sql import Delete, Insert, Update
from sqlalchemy.sql.selectable import Select

from fastsprout.data.backend.sql.entity import SQLEntity
from fastsprout.data.capabilities.query import BaseQuery

__all__ = ["SQLQuery"]


@dataclass
class SQLQuery[E: SQLEntity[Any]](BaseQuery[E, Select[tuple[E]]]):
    def _build(self) -> Select[tuple[E]]:
        return self._built_select.limit(
            getattr(self, "_limit_value", None),
        ).offset(
            getattr(self, "_offset_value", None),
        )

    @property
    def _built_select(self) -> Select[tuple[E]]:
        return select(self.entity)

    @property
    def _built_insert(self) -> Insert:
        return insert(self.entity.__table__)

    @property
    def _built_update(self) -> Update:
        return update(self.entity.__table__)

    @property
    def _built_delete(self) -> Delete:
        return delete(self.entity.__table__)
