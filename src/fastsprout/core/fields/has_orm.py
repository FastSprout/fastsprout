__all__ = ["HasOrm"]


class HasOrm[OrmCtor]:
    """Marker base: entity exposes ORM extension wrapper class.

    Subclasses bind OrmCtor to a concrete generic class. The fastsprout-core
    mypy plugin uses this binding to derive `.orm` types at access sites.
    """
