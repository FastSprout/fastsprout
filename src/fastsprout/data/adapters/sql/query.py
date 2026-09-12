from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import Select

from fastsprout.data.adapters.sql.entity import SQLEntity
from fastsprout.data.capabilities import BaseQuery

__all__ = ["SQLQuery"]


@dataclass
class SQLQuery[E: SQLEntity[Any]](BaseQuery[E, Select[tuple[E]]]):
    @property
    @override
    def builded_query(self):
        return select(self.entity)
