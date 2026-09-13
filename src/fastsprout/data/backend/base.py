from abc import ABC, abstractmethod
from typing import Any

from fastsprout.data.capabilities import BaseQuery
from fastsprout.data.entity import Entitieable

__all__ = ["BaseBackend"]


class BaseBackend[E: Entitieable[Any], Q: BaseQuery](ABC):
    entity: type[E]

    def __init_subclass__(cls, **kwargs: object):
        super().__init_subclass__(**kwargs)
        if (
            ABC in cls.__bases__
            or getattr(cls, "__abstractmethods__", None)
            or getattr(cls, "__parameters__", None)
        ):
            raise TypeError(f"{cls.__name__} is a Abstract Class")
        if not hasattr(cls, "entity") or cls.entity is None:
            raise TypeError(f"{cls.__name__} must define 'entity'")

    @property
    @abstractmethod
    def default_query(self) -> Q:
        raise NotImplementedError
