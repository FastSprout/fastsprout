from abc import ABC, abstractmethod
from typing import Any

from fastsprout.data.capabilities import BaseQuery
from fastsprout.data.entity import Entitieable

__all__ = ["BaseAdapter"]


class BaseAdapter[E: Entitieable[Any], Q: BaseQuery](ABC):
    entity: type[E]

    def __init_subclass__(cls, **kwargs: object):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "entity") or cls.entity is None:
            raise TypeError(f"{cls.__name__} must define 'entity'")

    @property
    @abstractmethod
    def default_query(self) -> Q:
        raise NotImplementedError
