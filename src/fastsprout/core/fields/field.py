from typing import Any, overload

from .field_assigment import FieldAssignment
from .field_ref import FieldRef
from .has_orm import HasOrm

__all__ = ["Field"]


class Field[T]:
    """Typed field descriptor.

    Annotation form: `is_active: Field[bool]`

    Behavior:
      - On class:    `Hero.is_active` → FieldRef[Hero, bool, OrmCtor]
        (carries entity binding for repository.select; mypy plugin refines
        `.orm` to `OrmCtor[T]` at access sites)
      - On instance: `hero.is_active` → bool (the value)

    Use `.set(value)` for partial-update assignment objects:
        Field("is_active").set(True)
    """

    __slots__ = ("_orm", "name")

    def __init__(self, name: str = "", orm: Any = None) -> None:
        self.name = name
        self._orm = orm

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def set(self, value: T) -> FieldAssignment[T]:
        return FieldAssignment(self.name, value)

    @overload
    def __get__[OrmCtor](
        self, instance: None, owner: type[HasOrm[OrmCtor]]
    ) -> FieldRef[Any, T, OrmCtor]: ...
    @overload
    def __get__[E](
        self, instance: None, owner: type[E]
    ) -> FieldRef[E, T, None]: ...
    @overload
    def __get__(self, instance: object, owner: type) -> T: ...
    def __get__(
        self, instance: object | None, owner: type
    ) -> FieldRef[Any, T, Any] | T:
        if instance is None:
            return FieldRef(self.name, owner, self._orm)
        try:
            return instance.__dict__[self.name]  # type: ignore[no-any-return]
        except KeyError as e:
            raise AttributeError(
                f"{type(instance).__name__!r} object has no attribute "
                f"{self.name!r}"
            ) from e

    def __set__(self, instance: object, value: T) -> None:
        instance.__dict__[self.name] = value

    def __repr__(self) -> str:
        return f"Field({self.name!r})"
