from typing import dataclass_transform

from fastsprout.core.fields import Field
from fastsprout.core.fields.metaclass import (
    collect_field_descriptors,
    install_descriptors,
    read_annotations,
    unwrap_field_annotations,
)

__all__ = ["typed_fields"]


def _apply_field_descriptors[C](cls: type[C]) -> type[C]:
    """Unwrap Field[T] annotations and install Field descriptors.

    Each descriptor preserves the EXACT declared Field subclass
    (e.g. PrivateField, SecretField, ReadOnlyField).
    """
    annotations = read_annotations(dict(cls.__dict__))
    field_descriptors = collect_field_descriptors(annotations)
    unwrap_field_annotations(annotations)
    install_descriptors(cls, field_descriptors)
    try:
        cls.__annotations__ = annotations
    except (AttributeError, TypeError):
        pass
    return cls


@dataclass_transform(kw_only_default=True, field_specifiers=(Field,))
def typed_fields[C](cls: type[C]) -> type[C]:
    """Install Field[T] descriptors on a plain class.

    You're responsible for __init__. No validation, no auto-generation.

    Example:
        @typed_fields
        class User:
            field_int: Field[int]
            field_str: Field[str]

            def __init__(self, field_int: int, field_str: str) -> None:
                self.field_int = field_int
                self.field_str = field_str
    """
    return _apply_field_descriptors(cls)
