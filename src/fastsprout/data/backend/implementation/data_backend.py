from abc import ABC

from fastsprout.data.entity import Signpostable

from ..protocols import Backendable, Finalizable

__all__ = ["BaseDataBackend"]


class BaseDataBackend[T, F: Finalizable](Backendable[T, F], ABC):
    """Base class for data backends.

    Class hierarchy may be abstract (framework machinery like SQLDataBackend
    and capability mixins), but only concrete classes — all type
    parameters bound, no abstract methods left — can be instantiated.
    """

    def __init__(self, /, signpost: Signpostable[T]) -> None:
        cls = type(self)
        if getattr(cls, "__abstractmethods__", None):
            raise TypeError(f"{cls.__name__} is an abstract backend")
        self._signpost = signpost
