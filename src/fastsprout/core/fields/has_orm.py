__all__ = ["HasOrm"]


class HasOrm[OrmCtor]:
    """Marker base: entity exposes ORM extension wrapper class.

    Field descriptors carry this binding to FieldRef.orm. The SQLAlchemy
    overload specializes Mapped to the field's value type; other wrappers
    retain their declared type arguments (for example, FakeOrm[Any]).
    """
