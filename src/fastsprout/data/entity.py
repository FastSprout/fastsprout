from collections.abc import Callable
from typing import Annotated, ClassVar, Literal, Protocol, runtime_checkable

from annotated_types import Ge

from fastsprout.core.fields.visibility import ReadField
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


@runtime_checkable
class Entitieable[ID: IdentificatableType](Protocol):
    """Anything with an identity.

    Note: the signpost (`__signpost__`) is intentionally NOT required
    here — streams and capabilities must work with backend-less
    entities; only the router looks it up.
    """

    __signpost__: ClassVar[Signpostable]

    @property
    def fastsprout_visibility(
        self,
    ) -> Literal[
        "entity",
        "read",
        "write",
        "read_write",
        "extra_read",
        "extra_write",
        "extra_read_write",
    ]: ...

    id: ReadField[ID]


class BaseEntity[ID: IdentificatableType](BaseSchema):
    # The signpost: any Signpostable — resolved by the router only,
    # invisible to pydantic (TYPE_CHECKING) and not a model field.
    __signpost__: ClassVar[Signpostable]

    id: ReadField[ID]
