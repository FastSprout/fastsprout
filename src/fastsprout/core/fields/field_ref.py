from __future__ import annotations

from fastsprout.core.types.comparable import FilterValue
from fastsprout.core.types.iterable import AnyIterable

from .conditions import Between, Eq, Gt, Gte, In, Lt, Lte, Ne
from .field_assigment import FieldAssignment
from .field_predicate import FieldPredicate

__all__ = ["FieldRef"]


class FieldRef[E, T, OrmCtor]:
    """Class-bound reference to a field and with generic ORM/backend extension.

    Carries entity class and field name. Value type T is static-only.
    Supports `.set(value)` like Field, mirroring API.

    Field.__get__ determines OrmCtor from the entity's HasOrm binding.
    SQLAlchemy fields use Mapped[T]; other wrappers retain their declared
    type arguments. Fields without an ORM binding use None.
    """

    __slots__ = ("entity_cls", "name", "orm")

    def __init__(self, name: str, entity_cls: type[E], orm: OrmCtor) -> None:
        self.name = name
        self.entity_cls = entity_cls
        self.orm: OrmCtor = orm

    def set(self, value: T) -> FieldAssignment[T]:
        return FieldAssignment(self.name, value)

    def eq[V: FilterValue](
        self: FieldRef[E, V, OrmCtor], value: V
    ) -> FieldPredicate[E]:
        return FieldPredicate(self.entity_cls, self.name, Eq(value))

    def ne[V: FilterValue](
        self: FieldRef[E, V, OrmCtor], value: V
    ) -> FieldPredicate[E]:
        return FieldPredicate(self.entity_cls, self.name, Ne(value))

    def gt[V: FilterValue](
        self: FieldRef[E, V, OrmCtor], value: V
    ) -> FieldPredicate[E]:
        return FieldPredicate(self.entity_cls, self.name, Gt(value))

    def gte[V: FilterValue](
        self: FieldRef[E, V, OrmCtor], value: V
    ) -> FieldPredicate[E]:
        return FieldPredicate(self.entity_cls, self.name, Gte(value))

    def lt[V: FilterValue](
        self: FieldRef[E, V, OrmCtor], value: V
    ) -> FieldPredicate[E]:
        return FieldPredicate(self.entity_cls, self.name, Lt(value))

    def lte[V: FilterValue](
        self: FieldRef[E, V, OrmCtor], value: V
    ) -> FieldPredicate[E]:
        return FieldPredicate(self.entity_cls, self.name, Lte(value))

    def in_[V: FilterValue](
        self: FieldRef[E, V, OrmCtor], values: AnyIterable[V]
    ) -> FieldPredicate[E]:
        """Match membership; finite iterators are cached on first evaluation."""
        return FieldPredicate(self.entity_cls, self.name, In(values))

    def between[V: FilterValue](
        self: FieldRef[E, V, OrmCtor], lower: V, upper: V
    ) -> FieldPredicate[E]:
        return FieldPredicate(self.entity_cls, self.name, Between(lower, upper))

    def __repr__(self) -> str:
        return f"<{self.entity_cls.__name__}.{self.name}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FieldRef):
            return NotImplemented
        return self.entity_cls is other.entity_cls and self.name == other.name

    def __hash__(self) -> int:
        return hash((self.entity_cls, self.name))
