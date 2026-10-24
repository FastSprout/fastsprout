"""Derive DTO classes at runtime while preserving the source type in IDEs."""

from types import new_class

from .base import DTO, ReadDTO, ReadWriteDTO, WriteDTO

__all__ = [
    "derive_dto",
    "derive_read_dto",
    "derive_read_write_dto",
    "derive_write_dto",
]


def derive_dto[E](entity: type[E], mode: type[DTO]) -> type[E]:
    """Cache each source and visibility combination independently.

    Visibility is enforced at runtime. For static field restrictions, declare
    a class inheriting from a visibility base and the source entity instead.
    """
    cache_key = f"__fastsprout_{mode.__name__}__"
    model = vars(entity).get(cache_key)
    if model is None:
        name = f"{entity.__name__}{mode.__name__.removesuffix('DTO')}"
        model = new_class(
            name,
            (mode, entity),
            exec_body=lambda namespace: namespace.update(
                __module__=entity.__module__
            ),
        )
        setattr(entity, cache_key, model)
    if not isinstance(model, type) or not issubclass(model, entity):
        raise TypeError("DTO must derive from its source entity")
    return model


def derive_read_dto[E](entity: type[E]) -> type[E]:
    """Derive a DTO exposing fields marked for reading."""
    return derive_dto(entity, ReadDTO)


def derive_write_dto[E](entity: type[E]) -> type[E]:
    """Derive a DTO exposing fields marked for writing."""
    return derive_dto(entity, WriteDTO)


def derive_read_write_dto[E](entity: type[E]) -> type[E]:
    """Derive a DTO exposing read and write fields, excluding internal fields."""
    return derive_dto(entity, ReadWriteDTO)
