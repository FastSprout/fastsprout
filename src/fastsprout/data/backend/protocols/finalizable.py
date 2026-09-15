from typing import Protocol, runtime_checkable

__all__ = ["Finalizable"]


@runtime_checkable
class Finalizable(Protocol):
    async def finalize(self) -> None: ...
    async def abort(self) -> None: ...
