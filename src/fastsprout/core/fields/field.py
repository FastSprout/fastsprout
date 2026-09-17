import contextvars
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, overload

from sqlalchemy.orm import Mapped

from fastsprout.core.types.undefined import Undefined, UndefinedType

from .field_assigment import FieldAssignment
from .field_ref import FieldRef
from .has_orm import HasOrm

__all__ = ["Field"]

model_building_context_var: contextvars.ContextVar[bool] = (
    contextvars.ContextVar("fastsprout_model_building", default=False)
)


class Field[T]:
    """Typed field descriptor.

    Annotation form: `is_active: Field[bool]`

    Behavior:
      - On class:    `Hero.is_active` → FieldRef[Hero, bool, OrmCtor]
        (carries entity binding for repository.select; the SQLAlchemy
        overload types `.orm` as `Mapped[T]`)
      - On instance: `hero.is_active` → bool (the value)

    Defaults are declared through the specifier, not raw assignment —
    this keeps both the type checker and the runtime model build happy:

        class Hero(BaseSchema):
            age: Field[int] = Field(default=0)
            uid: Field[UUID] = Field(default_factory=uuid4)

    Use `.set(value)` for partial-update assignment objects:
        Hero.is_active.set(True)        # FieldAssignment[bool]
    """

    __slots__ = ("_orm", "default", "default_factory", "name")

    def __init__(
        self,
        *,
        default: UndefinedType = Undefined,
        default_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.name = ""
        self._orm = None
        self.default = default
        self.default_factory = default_factory

    @classmethod
    def _descriptor(cls, name: str, orm: Any = None) -> "Field[Any]":
        """Internal: build the descriptor installed on model classes.

        Bypasses the public specifier constructor — framework use only
        (metaclasses), never part of the user-facing API.
        """
        self = cls.__new__(cls)
        self.name = name
        self._orm = orm
        self.default = Undefined
        self.default_factory = None
        return self

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def set(self, value: T) -> FieldAssignment[T]:
        return FieldAssignment(self.name, value)

    if TYPE_CHECKING:

        @overload
        def __get__(
            self, instance: None, owner: type[HasOrm[Mapped[Any]]]
        ) -> FieldRef[Any, T, Mapped[T]]: ...

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
            if model_building_context_var.get():
                raise AttributeError(self.name)
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
