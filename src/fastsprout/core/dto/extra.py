from typing import ClassVar, Literal

from .base import DTO

__all__ = ["ExtraReadDTO", "ExtraReadWriteDTO", "ExtraWriteDTO"]


class ExtraReadDTO(DTO):
    """Read fields including explicitly requested extra read fields."""

    __fastsprout_operations__: ClassVar[frozenset[str]] = frozenset(
        {"read", "extra_read"}
    )

    @property
    def fastsprout_visibility(self) -> Literal["extra_read"]:
        return "extra_read"


class ExtraWriteDTO(DTO):
    """Write fields including explicitly requested extra write fields."""

    __fastsprout_operations__: ClassVar[frozenset[str]] = frozenset(
        {"write", "extra_write"}
    )

    @property
    def fastsprout_visibility(self) -> Literal["extra_write"]:
        return "extra_write"


class ExtraReadWriteDTO(DTO):
    """Read and write fields including both kinds of extra fields."""

    __fastsprout_operations__: ClassVar[frozenset[str]] = frozenset(
        {"read", "write", "extra_read", "extra_write"}
    )

    @property
    def fastsprout_visibility(self) -> Literal["extra_read_write"]:
        return "extra_read_write"
