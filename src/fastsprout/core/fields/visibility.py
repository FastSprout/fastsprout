from typing import TYPE_CHECKING, Any, ClassVar, Literal, Protocol

from .field import Field

__all__ = [
    "DTOVisibility",
    "EntityVisibility",
    "InternalField",
    "ReadField",
    "Readable",
    "SQLReadable",
    "WriteField",
]


class DTOVisibility:
    """Identify DTO bases without importing DTO construction."""


class EntityVisibility:
    """Unrestricted source; DTO bases supply a concrete visibility mode.

    Only this private marker is Any. Field value types remain fully typed.
    The open marker allows a DTO to narrow visibility without an incompatible
    override of a literal-valued member on its source entity.
    """

    @property
    def fastsprout_visibility(self) -> Any:
        return "entity"


class Readable(Protocol):
    @property
    def fastsprout_visibility(
        self,
    ) -> Literal["entity", "read", "read_write"]: ...


if TYPE_CHECKING:
    from sqlalchemy import Table

    class SQLReadable(Readable, Protocol):
        __table__: ClassVar[Table]


class Writable(Protocol):
    @property
    def fastsprout_visibility(
        self,
    ) -> Literal["entity", "write", "read_write"]: ...


class Internal(Protocol):
    @property
    def fastsprout_visibility(self) -> Literal["entity"]: ...


class ReadField[T](Field[T, Readable]):
    """Included in read DTOs, excluded from write-only DTOs."""

    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"read"})


class WriteField[T](Field[T, Writable]):
    """Included in write DTOs, excluded from read-only DTOs."""

    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"write"})


class InternalField[T](Field[T, Internal]):
    """Accessible on the entity, excluded from every public DTO."""

    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"internal"})
