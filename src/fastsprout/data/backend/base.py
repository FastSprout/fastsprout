from abc import ABC

__all__ = ["BaseDataBackend"]


class BaseDataBackend(ABC):  # noqa: B024
    """Base class for data backends.

    Class hierarchy may be abstract (framework machinery like SQLDataBackend
    and capability mixins), but only concrete classes — all type
    parameters bound, no abstract methods left — can be instantiated.
    """

    def __init__(self) -> None:
        cls = type(self)
        if getattr(cls, "__abstractmethods__", None) or getattr(
            cls, "__parameters__", None
        ):
            raise TypeError(f"{cls.__name__} is an abstract backend")
