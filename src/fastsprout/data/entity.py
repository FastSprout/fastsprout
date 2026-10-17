from collections.abc import Callable
from typing import Annotated, ClassVar, Protocol, runtime_checkable

from annotated_types import Ge

from fastsprout.core.fields.visibility import EntityVisibility, ReadField
from fastsprout.core.schema import BaseSchema
from fastsprout.core.types.identificable import IdentificatableType

__all__ = ["BaseEntity", "Entitieable", "Signpostable"]


@runtime_checkable
class Signpostable[T](Protocol):
    def __init__(
        self, factory: Callable[[], T], *, priority: Annotated[int, Ge(0)] = 0
    ) -> None: ...

    priority: Annotated[int, Ge(0)] = 0

    def factory(self) -> T: ...


class Entitieable[ID: IdentificatableType](EntityVisibility):
    """Shared entity base, independent of storage and model validation."""

    __signpost__: ClassVar[Signpostable]

    id: ReadField[ID]


class BaseEntity[ID: IdentificatableType](BaseSchema, Entitieable[ID]):
    id: ReadField[ID]
