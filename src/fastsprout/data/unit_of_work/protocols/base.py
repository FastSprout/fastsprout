from types import TracebackType
from typing import Protocol, Self

from typing_extensions import runtime_checkable

__all__ = ["UnitOfWork"]


@runtime_checkable
class UnitOfWork[T, **P](Protocol):
    def __init__(self, *args: P.args, **kwargs: P.kwargs): ...

    @property
    def attrs_are_init(self) -> bool: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
