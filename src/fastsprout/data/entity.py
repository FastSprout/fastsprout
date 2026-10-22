from collections.abc import Callable
from typing import Annotated, Generic, Protocol, runtime_checkable

from annotated_types import Ge
from typing_extensions import TypeVar

from fastsprout.core.fields.visibility import EntityVisibility, ReadField
from fastsprout.core.schema import BaseSchema
from fastsprout.core.types.identificable import IdentificatableType

__all__ = ["BaseEntity", "Entitieable", "Signpostable"]

IDT = TypeVar("IDT", bound=IdentificatableType)
ResourceT = TypeVar("ResourceT", default=None)


@runtime_checkable
class Signpostable[T](Protocol):
    def __init__(
        self, factory: Callable[[], T], *, priority: Annotated[int, Ge(0)] = 0
    ) -> None: ...

    priority: Annotated[int, Ge(0)] = 0

    def factory(self) -> T: ...


class Entitieable[ID: IdentificatableType, Resource](EntityVisibility):
    """Shared entity base, independent of storage and model validation."""

    __signpost__: Signpostable[Resource]

    id: ReadField[ID]

    @classmethod
    def signpost(cls) -> Signpostable[Resource]:
        return cls.__signpost__


class BaseEntity(
    BaseSchema, Entitieable[IDT, ResourceT], Generic[IDT, ResourceT]
):
    id: ReadField[IDT]
