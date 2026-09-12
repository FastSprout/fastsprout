from abc import ABC, abstractmethod
from dataclasses import dataclass

from fastsprout.data.entity import Entitieable


@dataclass
class BaseQuery[E: Entitieable, QueryT](ABC):
    """Base for filters."""

    entity: type[E]

    @property
    @abstractmethod
    def builded_query(self) -> QueryT:
        raise NotImplementedError
