from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any, Self

from annotated_types import Ge

from fastsprout.data.entity import Entitieable


@dataclass
class BaseQuery[E: Entitieable[Any], StatementT](ABC):
    """Base for filters."""

    entity: type[E]
    statement: StatementT | None = field(default=None)

    def limit(self, max_n: Annotated[int, Ge(1)] = 1) -> Self:
        self._limit_value = max_n
        return self

    def offset(self, to: Annotated[int, Ge(0)] = 0) -> Self:
        self._offset_value = to
        return self

    @abstractmethod
    def _build(self) -> StatementT: ...

    @property
    def _built_query(self) -> StatementT:
        return self._build()
