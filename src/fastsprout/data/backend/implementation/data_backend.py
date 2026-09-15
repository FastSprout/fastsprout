from abc import ABC
from typing import Annotated

from annotated_types import Ge

from ..protocols import Backendable

__all__ = ["BaseDataBackend"]


class BaseDataBackend(Backendable, ABC):
    """Base class for data backends.

    Class hierarchy may be abstract (framework machinery like SQLDataBackend
    and capability mixins), but only concrete classes — all type
    parameters bound, no abstract methods left — can be instantiated.
    """

    priority: Annotated[int, Ge(0)] = 0

    def __init__(self) -> None:
        cls = type(self)
        if getattr(cls, "__abstractmethods__", None) or getattr(
            cls, "__parameters__", None
        ):
            raise TypeError(f"{cls.__name__} is an abstract backend")
