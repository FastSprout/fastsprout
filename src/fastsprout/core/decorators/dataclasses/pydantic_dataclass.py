from typing import cast, dataclass_transform

from pydantic.dataclasses import dataclass as _pyd_dataclass

from fastsprout.core.decorators.typed_fields import typed_fields
from fastsprout.core.fields import Field

__all__ = [
    "typed_pyd_dataclass",
    "typed_pydantic_dataclass",
]


@dataclass_transform(kw_only_default=True, field_specifiers=(Field,))
def typed_pydantic_dataclass[C](cls: type[C]) -> type[C]:
    """Apply pydantic @dataclass + install Field[T] descriptors.

    Auto-generated __init__ with runtime validation via Pydantic.
    Lighter than BaseSchema (no BaseModel overhead) but still validates.

    Example:
        @typed_pydantic_dataclass
        class User:
            field_int: Field[int]
            field_str: Field[str]

        User(field_int="not int", field_str="x")  # raises ValidationError
    """

    return cast(type[C], _pyd_dataclass(typed_fields(cls)))


typed_pyd_dataclass = typed_pydantic_dataclass
