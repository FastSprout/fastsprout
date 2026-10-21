"""Query write actions accepting a query or field conditions."""

from typing import overload

from fastsprout.core import Depends
from fastsprout.core.dto.conversion import writable_names
from fastsprout.core.fields.field_assigment import FieldAssignment
from fastsprout.core.fields.field_predicate import FieldPredicate
from fastsprout.data.capabilities.query import BaseQuery
from fastsprout.data.entity import Entitieable
from fastsprout.data.router import DataR
from fastsprout.data.types import Valuable

from ..protocols.owners import QueryOwnable
from . import queries

__all__ = ["delete_by_query", "update_by_query"]


@overload
async def delete_by_query[E: Entitieable, R: Valuable | Entitieable, Statement](
    self: QueryOwnable[E, R],
    query: BaseQuery[E, Statement],
    *,
    datar: DataR = Depends(),
) -> int: ...


@overload
async def delete_by_query[E: Entitieable, R: Valuable | Entitieable](
    self: QueryOwnable[E, R],
    query: FieldPredicate[E],
    /,
    *predicates: FieldPredicate[E],
    datar: DataR = Depends(),
) -> int: ...


async def delete_by_query[E: Entitieable, R: Valuable | Entitieable, Statement](
    self: QueryOwnable[E, R],
    query: BaseQuery[E, Statement] | FieldPredicate[E],
    *predicates: FieldPredicate[E],
    datar: DataR = Depends(),
) -> int:
    return await datar.ability(self.entity).delete_by_query(
        queries.validated(self, datar, query, *predicates)
    )


@overload
async def update_by_query[
    E: Entitieable,
    R: Valuable | Entitieable,
    Statement,
    Value,
](
    self: QueryOwnable[E, R],
    query: BaseQuery[E, Statement],
    /,
    *assignments: FieldAssignment[Value],
    datar: DataR = Depends(),
) -> int: ...


@overload
async def update_by_query[E: Entitieable, R: Valuable | Entitieable, Value](
    self: QueryOwnable[E, R],
    query: FieldPredicate[E],
    /,
    *assignments: FieldAssignment[Value] | FieldPredicate[E],
    datar: DataR = Depends(),
) -> int: ...


async def update_by_query[
    E: Entitieable,
    R: Valuable | Entitieable,
    Statement,
    Value,
](
    self: QueryOwnable[E, R],
    query: BaseQuery[E, Statement] | FieldPredicate[E],
    /,
    *assignments: FieldAssignment[Value] | FieldPredicate[E],
    datar: DataR = Depends(),
) -> int:
    predicates = tuple(
        item for item in assignments if isinstance(item, FieldPredicate)
    )
    updates = tuple(
        item for item in assignments if isinstance(item, FieldAssignment)
    )
    selection = queries.validated(self, datar, query, *predicates)
    if any(item.name not in writable_names(self.entity) for item in updates):
        raise AttributeError("Update field is not writable")
    return await datar.ability(self.entity).update_by_query(selection, *updates)
