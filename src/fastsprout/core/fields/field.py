import contextvars
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Self, overload

from sqlalchemy.orm import Mapped
from typing_extensions import TypeVar

from fastsprout.core.types.undefined import Undefined, UndefinedType

from .field_assigment import FieldAssignment
from .field_ref import FieldRef
from .has_orm import HasOrm

__all__ = ["Field"]

model_building_context_var: contextvars.ContextVar[bool] = (
    contextvars.ContextVar("fastsprout_model_building", default=False)
)


def check_field_visibility(owner: type, name: str) -> None:
    if name in vars(owner).get("__fastsprout_forbidden__", ()):
        operations = sorted(owner.__fastsprout_operations__)
        raise AttributeError(
            f"Field {name!r} not accessible in DTO (operations: {operations})"
        )


T = TypeVar("T")
FieldOwner = TypeVar("FieldOwner", default=object)


class Field(Generic[T, FieldOwner]):  # default type parameter on Python 3.12
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
    __fastsprout_ops__: ClassVar[frozenset[str]] = frozenset({"read", "write"})

    def __init__(
        self,
        *,
        default: T | UndefinedType = Undefined,
        default_factory: Callable[[], T] | None = None,
    ) -> None:
        self.name = ""
        self._orm = None
        self.default = default
        self.default_factory = default_factory

    @classmethod
    def _descriptor(cls, name: str, orm: Any = None) -> Self:
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
            self: "Field[T, object]",
            instance: None,
            owner: type[HasOrm[Mapped[Any]]],
        ) -> FieldRef[Any, T, Mapped[T]]: ...

    @overload
    def __get__[OrmCtor](
        self: "Field[T, object]", instance: None, owner: type[HasOrm[OrmCtor]]
    ) -> FieldRef[Any, T, OrmCtor]: ...
    @overload
    def __get__[E](
        self: "Field[T, object]", instance: None, owner: type[E]
    ) -> FieldRef[E, T, None]: ...
    @overload
    def __get__(
        self, instance: None, owner: type[FieldOwner]
    ) -> FieldRef[FieldOwner, T, Any]: ...
    @overload
    def __get__(self, instance: FieldOwner, owner: type[FieldOwner]) -> T: ...
    def __get__(
        self, instance: object | None, owner: type
    ) -> FieldRef[Any, T, Any] | T:
        if model_building_context_var.get() and instance is None:
            raise AttributeError(self.name)
        self._check_visibility(owner)
        if instance is None:
            return FieldRef(self.name, owner, self._orm)
        try:
            return instance.__dict__[self.name]  # type: ignore[no-any-return]
        except KeyError as e:
            raise AttributeError(
                f"{type(instance).__name__!r} object has no attribute "
                f"{self.name!r}"
            ) from e

    def _check_visibility(self, owner: type) -> None:
        check_field_visibility(owner, self.name)

    def __set__(self, instance: FieldOwner, value: T) -> None:
        self._check_visibility(type(instance))
        instance.__dict__[self.name] = value

    def __repr__(self) -> str:
        return f"Field({self.name!r})"
