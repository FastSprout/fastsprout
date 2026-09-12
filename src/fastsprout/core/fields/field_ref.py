from .field_assigment import FieldAssignment

__all__ = ["FieldRef"]


class FieldRef[E, T, OrmCtor]:
    """Class-bound reference to a field and with generic ORM/backend extension.

    Carries entity class and field name. Value type T is static-only.
    Supports `.set(value)` like Field, mirroring API.

    ORM typeparam is filled by backend type aliases:
        type Field[T] = CoreField[T, Mapped[T]]   # fastsprout-data-sql
        type Field[T] = CoreField[T, MongoExpr[T]] # fastsprout-data-mongo
    """

    __slots__ = ("entity_cls", "name", "orm")

    def __init__(self, name: str, entity_cls: type[E], orm: OrmCtor) -> None:
        self.name = name
        self.entity_cls = entity_cls
        self.orm: OrmCtor = orm

    def set(self, value: T) -> FieldAssignment[T]:
        return FieldAssignment(self.name, value)

    def __repr__(self) -> str:
        return f"<{self.entity_cls.__name__}.{self.name}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FieldRef):
            return NotImplemented
        return self.entity_cls is other.entity_cls and self.name == other.name

    def __hash__(self) -> int:
        return hash((self.entity_cls, self.name))
