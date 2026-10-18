"""Query actions and read projection shared by DataSs."""

from fastsprout.core import (
    Depends,
    IdentificatorType,
    Undefined,
    UndefinedType,
)
from fastsprout.core.dto.base import DTO
from fastsprout.core.dto.conversion import field_names, project_read
from fastsprout.data.capabilities.query import (
    And,
    BaseQuery,
    Expression,
    FieldPredicate,
    Not,
    Or,
)
from fastsprout.data.entity import Entitieable
from fastsprout.data.router import DataR
from fastsprout.data.streams.protocols import AsyncEntityStream
from fastsprout.data.types import Valuable
from fastsprout.data.utils.callable import resolve_any_callable

from ..protocols.owners import PageOwner, QueryOwner
from ..schemas import read_source
from ..types import Page
from .payloads import find_entity

__all__ = [
    "count",
    "exists",
    "find_first",
    "get",
    "list",
    "public_condition",
    "selected",
    "stream",
    "validated",
]


def validated[
    E: Entitieable,
    R: Valuable | Entitieable,
    Statement,
](
    self: QueryOwner[E, R],
    datar: DataR,
    query: BaseQuery[E, Statement] | None,
) -> BaseQuery[E, Statement]:
    if query is not None and query.entity is not self.entity:
        raise TypeError("Query must select the CRUD entity")
    ability = datar.ability(self.entity)
    query = ability.query_for(self.entity) if query is None else query
    read = read_source(self.read_schema, self.entity)
    if any(
        name not in field_names(read, "read") for name, _ in query.orderings
    ):
        raise AttributeError("Sort field is not a public field")
    query = query.copy()
    query.conditions = tuple(
        public_condition(self.entity, read, condition)
        for condition in query.conditions
    )
    return query


def stream[E: Entitieable, R: Valuable | Entitieable, Statement](
    self: QueryOwner[E, R], datar: DataR, query: BaseQuery[E, Statement] | None
) -> AsyncEntityStream[E]:
    return datar.stream(validated(self, datar, query).unpaged())


async def count[
    E: Entitieable,
    R: Valuable | Entitieable,
    Statement,
](
    self: QueryOwner[E, R],
    query: BaseQuery[E, Statement] | None = None,
    *,
    datar: DataR = Depends(),
) -> int:
    return await stream(self, datar, query).count()


async def list[
    E: Entitieable,
    R: Valuable | Entitieable,
    Statement,
](
    self: PageOwner[E, R],
    query: BaseQuery[E, Statement] | None = None,
    *,
    datar: DataR = Depends(),
) -> Page[R]:
    offset = query.offset_value if query is not None else 0
    limit = query.limit_value if query is not None else Undefined
    page = (
        self.page_schema(items=[], total=0, offset=offset)
        if isinstance(limit, UndefinedType)
        else self.page_schema(items=[], total=0, offset=offset, limit=limit)
    )
    selection = validated(self, datar, query)
    total = await datar.stream(selection.unpaged()).count()
    rows = datar.stream(selection.offset(page.offset).limit(page.limit))
    items = [project_read(item, self.read_schema) async for item in rows]
    return self.page_schema(
        items=items, total=total, offset=page.offset, limit=page.limit
    )


async def find_first[
    E: Entitieable,
    R: Valuable | Entitieable,
    Statement,
](
    self: QueryOwner[E, R],
    query: BaseQuery[E, Statement],
    *,
    datar: DataR = Depends(),
) -> R | None:
    found = await datar.ability(self.entity).find_first(
        validated(self, datar, query)
    )
    return None if found is None else project_read(found, self.read_schema)


def selected[
    E: Entitieable,
    R: Valuable | Entitieable,
    Statement,
](
    self: QueryOwner[E, R], datar: DataR, query: BaseQuery[E, Statement]
) -> AsyncEntityStream[E]:
    return datar.stream(validated(self, datar, query))


async def get[E: Entitieable, R: Valuable | Entitieable, Statement](
    self: QueryOwner[E, R],
    identifier: IdentificatorType | BaseQuery[E, Statement],
    datar: DataR = Depends(),
) -> R | None:
    if isinstance(identifier, BaseQuery):
        return await find_first(self, identifier, datar=datar)
    found = await find_entity(self.entity, identifier, datar)
    return None if found is None else project_read(found, self.read_schema)


async def exists[E: Entitieable, R: Valuable | Entitieable, Statement](
    self: QueryOwner[E, R],
    identifier: IdentificatorType | BaseQuery[E, Statement],
    datar: DataR = Depends(),
) -> bool:
    if isinstance(identifier, BaseQuery):
        return await selected(self, datar, identifier).first() is not None
    return await find_entity(self.entity, identifier, datar) is not None


def public_condition[E: Entitieable](
    source: type[E],
    read: type[DTO | Entitieable],
    condition: Expression[E],
) -> Expression[E]:
    if isinstance(condition, Not):
        return Not(public_condition(source, read, condition.condition))
    if isinstance(condition, And | Or):
        return type(condition)(
            *(
                public_condition(source, read, child)
                for child in condition.conditions
            )
        )
    return public_leaf(source, read, condition)


def public_leaf[E: Entitieable](
    source: type[E],
    read: type[DTO | Entitieable],
    condition: Expression[E],
) -> Expression[E]:
    if isinstance(condition, FieldPredicate):
        return public_field(source, read, condition)
    if callable(condition):

        async def visible(entity: E) -> bool:
            public = project_read(entity, read)
            if not isinstance(public, source):
                raise TypeError("Read DTO must derive from the query entity")
            return await resolve_any_callable(condition)(public)

        return visible
    raise TypeError("Query conditions require field comparisons or predicates")


def public_field[E: Entitieable](
    source: type[E],
    read: type[DTO | Entitieable],
    condition: FieldPredicate[E],
) -> FieldPredicate[E]:
    if condition.source is not source:
        raise TypeError("Query field must belong to the service entity")
    if condition.name not in field_names(read, "read"):
        raise AttributeError(f"Field {condition.name!r} is not a public field")
    return condition
