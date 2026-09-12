from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel, to_snake

from fastsprout.core.fields.metaclass import TypedModelMeta

__all__ = ["BaseSchema"]


class BaseSchema(BaseModel, metaclass=TypedModelMeta):
    """Base schema with type-safe field descriptors.

    Subclasses declare fields with Field[T] annotations:

        class Hero(BaseSchema):
            id: Field[UUID]
            is_active: Field[bool]
            name: Field[str]

    Then:
        hero = Hero(id=uuid(), is_active=True, name="SuperMan")
        hero.is_active                  # bool
        Hero.is_active                  # Field[bool]
        Hero.is_active.set(True)        # FieldAssignment[bool]
    """

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            alias=to_snake,
            validation_alias=to_camel,
            serialization_alias=to_camel,
        ),
        populate_by_name=True,
    )
