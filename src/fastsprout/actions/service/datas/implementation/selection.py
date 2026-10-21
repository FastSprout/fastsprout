"""Map read results and join queries using public fields."""

from collections.abc import AsyncGenerator, Hashable
from contextlib import aclosing

from fastsprout.core import Depends, Schema
from fastsprout.core.depends.invocation import stream_dependencies
from fastsprout.core.dto.conversion import field_names, project_read
from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable
from fastsprout.data.router import DataR
from fastsprout.data.types import MapperCallable, Valuable
from fastsprout.data.utils.callable import resolve_any_callable
from fastsprout.data.utils.iterable import resolve_any_iterable

from ..protocols.owners import QueryOwnable
from ..schemas import read_source
from .queries import public_condition, selected, validated

__all__ = ["join", "map"]


@stream_dependencies
async def map[
    E: Entitieable,
    R: Valuable | Entitieable,
    O: Schema,
    Statement,
](
    self: QueryOwnable[E, R],
    query: BaseQuery[E, Statement],
    mapper: MapperCallable[R, O],
    *,
    datar: DataR = Depends(),
) -> AsyncGenerator[O, None]:
    resolved_mapper = resolve_any_callable(mapper)
    async with aclosing(
        resolve_any_iterable(selected(self, datar, query))
    ) as rows:
        async for entity in rows:
            yield await resolved_mapper(project_read(entity, self.read_schema))


@stream_dependencies
async def join[
    E: Entitieable,
    R: Valuable | Entitieable,
    F: Entitieable,
    Left,
    Right,
    Key: Hashable,
    LeftOrm,
    RightOrm,
](
    self: QueryOwnable[E, R],
    query: BaseQuery[E, Left],
    other: BaseQuery[F, Right],
    *,
    on: tuple[FieldRef[E, Key, LeftOrm], FieldRef[F, Key, RightOrm]],
    datar: DataR = Depends(),
) -> AsyncGenerator[tuple[R, F], None]:
    left_field, right_field = on
    right_schema = other.entity
    read = read_source(right_schema, other.entity)
    if left_field.name not in field_names(
        read_source(self.read_schema, self.entity), "read"
    ):
        raise AttributeError("Join field is not a public field")
    if any(
        name not in field_names(read, "read")
        for name in (
            right_field.name,
            *(name for name, _ in other.orderings),
        )
    ):
        raise AttributeError("Join field is not a public field")
    other = other.copy()
    other.conditions = tuple(
        public_condition(other.entity, read, condition)
        for condition in other.conditions
    )
    rows = datar.stream(validated(self, datar, query)).join(
        datar.stream(other), on=on
    )
    async with aclosing(resolve_any_iterable(rows)) as joined:
        async for left, right in joined:
            yield (
                project_read(left, self.read_schema),
                project_read(right, right_schema),
            )
