"""Configure CRUD schemas and enabled operations."""

import inspect
from collections.abc import Callable, Mapping
from functools import wraps
from typing import TYPE_CHECKING, get_args, get_origin

from fastsprout.core import Schema, UndefinedType
from fastsprout.data.entity import Entitieable
from fastsprout.data.types import Valuable

from ..schemas import configure_schemas, read_source
from ..types import DataSOperation, SchemaSetting

if TYPE_CHECKING:
    from .service import DataS

__all__ = [
    "DATAS_OPERATIONS",
    "ENTITY_ATTRIBUTE",
    "configure_service",
    "inherit_entity",
]

ENTITY_ATTRIBUTE = "entity_type"

DATAS_OPERATIONS: frozenset[DataSOperation] = frozenset(
    get_args(DataSOperation.__value__)
)


def guard_action[**Args, Result](
    name: str,
    enabled: Callable[[], bool],
    handler: Callable[Args, Result],
) -> Callable[Args, Result]:
    @wraps(handler)
    def call(*args: Args.args, **kwargs: Args.kwargs) -> Result:
        if not enabled():
            raise AttributeError(f"CRUD operation {name!r} is disabled")
        return handler(*args, **kwargs)

    return call


def inherit_entity[T](target: type[T], source: type[T]) -> None:
    for base in target.__mro__:
        for original in vars(base).get("__orig_bases__", ()):
            if get_origin(original) is source:
                entity = get_args(original)[0]
                if inspect.isclass(entity):
                    setattr(target, ENTITY_ATTRIBUTE, entity)
                    return


def configure_service[
    E: Entitieable,
    R: Valuable | Entitieable,
    C: Schema | Entitieable,
    U: Schema | Entitieable,
    P: Schema | Entitieable,
    CreateSetting: UndefinedType | None,
](
    self: "DataS[E, R, C, U, P, CreateSetting]",
    overrides: Mapping[str, SchemaSetting[R | C | U | P]],
    operations: frozenset[DataSOperation] | None,
) -> None:
    disabled = configure_schemas(self, self.entity, overrides)
    read_source(self.read_schema, self.entity)
    self.operations = (
        self.operations if operations is None else operations
    ) - disabled
    for operation in DATAS_OPERATIONS:

        def enabled(operation: DataSOperation = operation) -> bool:
            return operation in self.operations and operation not in disabled

        handler = guard_action(operation, enabled, getattr(self, operation))
        setattr(self, operation, handler)
