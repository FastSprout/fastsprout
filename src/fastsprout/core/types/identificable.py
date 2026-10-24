from typing import Annotated, Never

import pydantic_core.core_schema as core_schema
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from typing_extensions import TypeForm

from .protocols.identificable import Identificatable

__all__ = ["IDType", "IdentificatableType", "IdentificatorType", "PublicIDType"]


class IdentificatablePydanticValidator:
    @classmethod
    def __get_pydantic_core_schema__[T](
        cls, source: TypeForm[T], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Defines how Pydantic should validate the Identificatable interface."""

        def validate_protocol[V](v: V) -> V:
            # Enforce the runtime_checkable protocol check explicitly
            if v is None or not isinstance(v, Identificatable):
                raise ValueError(
                    "Object does not implement the Identificatable protocol"
                )
            return v

        return core_schema.no_info_after_validator_function(
            validate_protocol,
            schema=core_schema.any_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """Defines how the protocol maps out in OpenAPI / JSON schemas."""
        field_schema = handler(core_schema)
        field_schema.update(
            type="string",
            description="Any unique object conforming to the Identificatable interface",
        )
        return field_schema


IdentificatableType = Annotated[
    Identificatable[Never], IdentificatablePydanticValidator
]


type IdentificatorType = IdentificatableType
type IDType = IdentificatableType
type PublicIDType = IdentificatableType
