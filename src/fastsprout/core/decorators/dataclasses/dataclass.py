from dataclasses import dataclass as _stdlib_dataclass
from typing import dataclass_transform

from fastsprout.core.decorators.typed_fields import typed_fields
from fastsprout.core.fields import Field

__all__ = ["typed_dataclass"]


@dataclass_transform(kw_only_default=True, field_specifiers=(Field,))
def typed_dataclass[C](cls: type[C]) -> type[C]:
    """Apply stdlib @dataclass + install Field[T] descriptors.

    Auto-generated __init__, __repr__, __eq__. No runtime validation.

    Example:
        @typed_dataclass
        class User:
            field_int: Field[int]
            field_str: Field[str]
    """

    return _stdlib_dataclass(typed_fields(cls))
