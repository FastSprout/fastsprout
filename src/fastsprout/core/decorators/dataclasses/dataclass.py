from collections.abc import Callable
from dataclasses import dataclass as stdlib_dataclass
from dataclasses import field as stdlib_field
from typing import dataclass_transform, overload

from fastsprout.core.fields import Field
from fastsprout.core.fields.metaclass import (
    collect_field_descriptors,
    install_descriptors,
    read_annotations,
    unwrap_field_annotations,
)
from fastsprout.core.types.undefined import Undefined

__all__ = ["typed_dataclass"]


@overload
def typed_dataclass[C](
    cls: type[C], *, frozen: bool = False, kw_only: bool = False
) -> type[C]: ...


@overload
def typed_dataclass[C](
    cls: None = None, *, frozen: bool = False, kw_only: bool = False
) -> Callable[[type[C]], type[C]]: ...


@dataclass_transform(field_specifiers=(Field,))
def typed_dataclass[C](
    cls: type[C] | None = None,
    *,
    frozen: bool = False,
    kw_only: bool = False,
) -> type[C] | Callable[[type[C]], type[C]]:
    """Apply stdlib @dataclass + install Field[T] descriptors.

    Auto-generated __init__, __repr__, __eq__. No runtime validation.

    Example:
        @typed_dataclass
        class User:
            field_int: Field[int]
            field_str: Field[str]
    """

    def decorate(source: type[C]) -> type[C]:
        return decorate_dataclass(source, frozen=frozen, kw_only=kw_only)

    return decorate if cls is None else decorate(cls)


def decorate_dataclass[C](
    cls: type[C], *, frozen: bool, kw_only: bool
) -> type[C]:
    annotations = read_annotations(dict(vars(cls)))
    descriptors = collect_field_descriptors(annotations)
    unwrap_field_annotations(annotations)
    cls.__annotations__ = annotations
    for name in descriptors:
        specifier = vars(cls).get(name)
        if not isinstance(specifier, Field):
            continue
        if specifier.default_factory is not None:
            setattr(
                cls,
                name,
                stdlib_field(default_factory=specifier.default_factory),
            )
        elif specifier.default is not Undefined:
            setattr(cls, name, specifier.default)
        else:
            delattr(cls, name)
    result = stdlib_dataclass(cls, frozen=frozen, kw_only=kw_only)
    install_descriptors(result, descriptors)
    return result
