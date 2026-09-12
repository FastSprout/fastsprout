from fastsprout.core.fields.field import Field
from fastsprout.core.schema import BaseSchema
from fastsprout.core.types.identificable import IdentificatableType

__all__ = ["BaseEntity"]


class BaseEntity[ID: IdentificatableType](BaseSchema):
    id: Field[ID]
