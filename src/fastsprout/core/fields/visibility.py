from typing import Any, ClassVar, Literal, Protocol

from .field import Field

__all__ = ["EntityVisibility", "InternalField", "ReadField", "WriteField"]


class EntityVisibility:
    """Unrestricted source; DTO bases supply a concrete visibility mode.

    Only this private marker is Any. Field value types remain fully typed.
    The open marker allows a DTO to narrow visibility without an incompatible
    override of a literal-valued member on its source entity.
    """

    @property
    def _fastsprout_visibility(self) -> Any:
        return "entity"


class _Readable(Protocol):
    @property
    def _fastsprout_visibility(
        self,
    ) -> Literal["entity", "read", "read_write"]: ...


class _Writable(Protocol):
    @property
    def _fastsprout_visibility(
        self,
    ) -> Literal["entity", "write", "read_write"]: ...


class _Internal(Protocol):
    @property
    def _fastsprout_visibility(self) -> Literal["entity"]: ...


class ReadField[T](Field[T, _Readable]):
    """Included in read DTOs, excluded from write-only DTOs."""

    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"read"})


class WriteField[T](Field[T, _Writable]):
    """Included in write DTOs, excluded from read-only DTOs."""

    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"write"})


class InternalField[T](Field[T, _Internal]):
    """Accessible on the entity, excluded from every public DTO."""

    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"internal"})
