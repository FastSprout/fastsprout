from typing import Protocol, runtime_checkable

from fastsprout.core.fields.field import Field
from fastsprout.core.schema import BaseSchema
from fastsprout.core.types.identificable import IdentificatableType

__all__ = ["BaseEntity", "Entitieable"]


@runtime_checkable
class Entitieable[ID: IdentificatableType](Protocol):
    id: Field[ID]


class BaseEntity[ID: IdentificatableType](BaseSchema):
    id: Field[ID]
