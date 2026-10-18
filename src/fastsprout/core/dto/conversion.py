"""Convert explicit schemas while preserving field visibility and supplied values."""

from ..fields.field import Field
from ..fields.visibility import EntityVisibility
from ..types.schema import Schema
from .base import DTO, ReadDTO, ReadWriteDTO, WriteDTO

__all__ = [
    "field_names",
    "prepare_create",
    "prepare_update",
    "project_read",
    "supplied_names",
    "writable_names",
]


def field_names(
    source: type[Schema | EntityVisibility], operation: str
) -> frozenset[str]:
    if issubclass(source, DTO):
        return source.__fastsprout_definition__.allowed
    fields = {
        name: field.__fastsprout_ops__
        for base in reversed(source.__mro__)
        for name, field in vars(base).items()
        if isinstance(field, Field)
    }
    for base in reversed(source.__mro__):
        for name, field in (
            vars(base).get("__fastsprout_descriptors__", {}).items()
        ):
            fields.setdefault(name, field.__fastsprout_ops__)
    return frozenset(
        name for name, operations in fields.items() if operation in operations
    )


def project_read[R](entity: Schema | EntityVisibility, read: type[R]) -> R:
    if isinstance(entity, read):
        return entity
    if (
        not issubclass(read, DTO)
        or "read" not in read.__fastsprout_operations__
    ):
        raise TypeError("Read projection requires a ReadDTO")
    return read(
        **{
            name: getattr(entity, name)
            for name in read.__fastsprout_definition__.allowed
        }
    )


def writable_names(entity: type[Schema | EntityVisibility]) -> frozenset[str]:
    return field_names(entity, "write")


def supplied_names(payload: Schema | EntityVisibility) -> set[str]:
    if isinstance(payload, ReadDTO | WriteDTO | ReadWriteDTO):
        return set(vars(payload))
    return set(getattr(payload, "model_fields_set", vars(payload)))


def check_write_names[E: Schema | EntityVisibility](
    source: type[E], names: set[str]
) -> None:
    forbidden = names - writable_names(source)
    if forbidden:
        raise AttributeError(f"Field {sorted(forbidden)[0]!r} is not writable")


def prepare_create[E: Schema | EntityVisibility, C: Schema | EntityVisibility](
    source: type[E], schema: type[C], data: E | C
) -> E:
    if isinstance(data, source):
        return source(**vars(data)) if isinstance(data, WriteDTO) else data
    names = supplied_names(data)
    check_write_names(source, names)
    normalized = schema(**{name: getattr(data, name) for name in names})
    return source(
        **{name: getattr(normalized, name) for name in vars(normalized)}
    )


def prepare_update[E: Schema | EntityVisibility, U: Schema | EntityVisibility](
    source: type[E],
    schema: type[U],
    data: E | U,
    stored: E,
    *,
    partial: bool = False,
) -> E:
    names = supplied_names(data)
    if isinstance(data, source):
        names &= writable_names(source)
    check_write_names(source, names)
    normalized = schema(**{name: getattr(data, name) for name in names})
    supplied = supplied_names(normalized) if partial else set(vars(normalized))
    if isinstance(normalized, source):
        supplied &= writable_names(source)
    check_write_names(source, supplied)
    values = {
        **{
            name: value
            for name, value in vars(stored).items()
            if not name.startswith("_")
        },
        **{name: getattr(normalized, name) for name in supplied},
    }
    return source(**values)
