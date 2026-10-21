from typing import TYPE_CHECKING, Any, ClassVar, Literal, Protocol

from .field import Field

__all__ = [
    "DTOVisibility",
    "EntityVisibility",
    "ExtraReadField",
    "ExtraReadable",
    "ExtraWritable",
    "ExtraWriteField",
    "InternalField",
    "ReadField",
    "Readable",
    "SQLExtraReadable",
    "SQLExtraWritable",
    "SQLFieldable",
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
    ) -> Literal[
        "entity", "read", "read_write", "extra_read", "extra_read_write"
    ]: ...


class ExtraReadable(Protocol):
    @property
    def fastsprout_visibility(
        self,
    ) -> Literal["entity", "extra_read", "extra_read_write"]: ...


class ExtraWritable(Protocol):
    @property
    def fastsprout_visibility(
        self,
    ) -> Literal["entity", "extra_write", "extra_read_write"]: ...


if TYPE_CHECKING:
    from sqlalchemy import Table

    class SQLFieldable(Protocol):
        __table__: ClassVar[Table]

    class SQLReadable(Readable, SQLFieldable, Protocol): ...

    class SQLExtraReadable(ExtraReadable, SQLFieldable, Protocol): ...

    class SQLExtraWritable(ExtraWritable, SQLFieldable, Protocol): ...


class Writable(Protocol):
    @property
    def fastsprout_visibility(
        self,
    ) -> Literal[
        "entity", "write", "read_write", "extra_write", "extra_read_write"
    ]: ...


class Internalable(Protocol):
    @property
    def fastsprout_visibility(self) -> Literal["entity"]: ...


class ReadField[T](Field[T, Readable]):
    """Included in read DTOs, excluded from write-only DTOs."""

    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"read"})


class WriteField[T](Field[T, Writable]):
    """Included in write DTOs, excluded from read-only DTOs."""

    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"write"})


class InternalField[T](Field[T, Internalable]):
    """Accessible on the entity, excluded from every public DTO."""

    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"internal"})


class ExtraReadField[T](Field[T, ExtraReadable]):
    """Excluded from ordinary DTOs; requires extended read visibility."""

    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"extra_read"})


class ExtraWriteField[T](Field[T, ExtraWritable]):
    """Excluded from ordinary DTOs; requires extended write visibility."""

    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"extra_write"})
