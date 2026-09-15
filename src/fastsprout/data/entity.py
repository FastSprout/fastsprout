from typing import TYPE_CHECKING, ClassVar, Protocol, runtime_checkable

from fastsprout.core.fields.field import Field
from fastsprout.core.schema import BaseSchema
from fastsprout.core.types.identificable import IdentificatableType

if TYPE_CHECKING:
    from fastsprout.data.backend.protocols import Backendable
else:
    Backendable = object

__all__ = ["BaseEntity", "Entitieable"]


@runtime_checkable
class Entitieable[ID: IdentificatableType](Protocol):
    """Anything with an identity.

    Note: the signpost (`__backend__`) is intentionally NOT required
    here — streams and capabilities must work with backend-less
    entities; only the router looks it up.
    """

    id: Field[ID]


class BaseEntity[ID: IdentificatableType](BaseSchema):
    if TYPE_CHECKING:
        # The signpost: any Backendable — resolved by the router only,
        # invisible to pydantic (TYPE_CHECKING) and not a model field.
        __backend__: ClassVar[Backendable]

    id: Field[ID]
