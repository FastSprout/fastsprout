from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from fastsprout.data.entity import BaseEntity


@dataclass
class BaseQuery[E: BaseEntity[Any], QueryT](ABC):
    """Base for filters."""

    entity: type[E]

    @property
    @abstractmethod
    def builded_query(self) -> QueryT:
        raise NotImplementedError
