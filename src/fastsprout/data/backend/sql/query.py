from collections.abc import Hashable
from contextlib import AbstractAsyncContextManager
from typing import Any, Generic, Never, Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from typing_extensions import TypeVar

from fastsprout.core import UndefinedType, dataclass
from fastsprout.core.fields.field_ref import FieldComparison
from fastsprout.data.capabilities.query import (
    And,
    BaseQuery,
    Expression,
    FieldPredicate,
    Filter,
)
from fastsprout.data.entity import Signpostable
from fastsprout.data.streams.implementation import JoinedStream
from fastsprout.data.types import PredicateCallable

from .data_backend import SQLDataBackend
from .entity import SQLEntity, SQLSource, validate_source
from .predicates import compile_predicate, row_filter

__all__ = ["SQLJoinedQuery", "SQLQuery", "compile_predicate"]

E = TypeVar("E", bound=SQLEntity[Any])
SourceT = TypeVar("SourceT", bound=SQLSource, default=SQLSource)


@dataclass
class SQLQuery(BaseQuery[E, Select[tuple[E]]], Generic[E, SourceT]):
    """Use source= to check join target types and pin the signpost instance."""

    source: SourceT | None = None

    @property
    def native_conditions(self) -> bool:
        condition: Expression[E] = And(*self.conditions)
        return (
            compile_predicate(
                condition,
                self.entity,
                lambda name: self.entity.__table__.c[name],
            )
            is not None
        )

    def build(self) -> Select[tuple[E]]:
        validate_source(self.entity, self.source)
        statement = (
            self.statement
            if self.statement is not None
            else select(self.entity)
        )
        return apply_query(self, statement)

    def join[F: SQLEntity[Any], L: SQLEntity[Any], Key: Hashable, LO, RO](
        self,
        entity: type[SQLEntity[Any, SourceT]],
        condition: FieldComparison[L, F, Key, LO, RO],
    ) -> "SQLJoinedQuery[SourceT, FieldPredicate[F], E, F]":
        row_conditions: tuple[Filter[Never], ...] = ()
        return join_query(
            self,
            entity,
            condition,
            source=self.source,
            row_conditions=row_conditions,
        )


@dataclass
class SQLJoinedQuery[S: SQLSource, P: FieldPredicate, E: SQLEntity[Any], *Ts](
    BaseQuery[E, Select[tuple[E, *Ts]], tuple[E, *Ts]]
):
    """Filter fields from joined entities; Python callbacks receive the root."""

    sources: tuple[type[SQLEntity[Any]], ...] = ()
    source: S | None = None
    row_conditions: tuple[Filter[P | PredicateCallable[E]], ...] = ()

    def where(self, *conditions: Filter[P | PredicateCallable[E]]) -> Self:
        self.row_conditions += conditions
        return self

    def unfiltered(self) -> Self:
        query = super().unfiltered()
        query.row_conditions = ()
        return query

    @property
    def native_conditions(self) -> bool:
        root = SQLQuery(
            self.entity, conditions=self.conditions
        ).native_conditions
        condition: Filter[P | PredicateCallable[E]] = And(*self.row_conditions)
        joined = compile_predicate(
            condition,
            self.sources,
            lambda name: self.entity.__table__.c[name],
        )
        return root and joined is not None

    def stream(
        self, signpost: Signpostable[AbstractAsyncContextManager[AsyncSession]]
    ) -> JoinedStream[E, *Ts]:
        return SQLDataBackend(signpost).stream_rows(
            self,
            native_conditions=self.native_conditions,
            condition=row_filter(And(*self.row_conditions), self.sources),
        )

    def build(self) -> Select[tuple[E, *Ts]]:
        validate_source(self.entity, self.source)
        for source in self.sources:
            validate_source(source)
            if source.__signpost__ is not self.entity.__signpost__:
                raise TypeError("SQL joins require one shared signpost")
        if self.statement is None:
            raise TypeError("A joined query requires a SQL statement")
        condition: Filter[P | PredicateCallable[E]] = And(*self.row_conditions)
        joined = compile_predicate(
            condition,
            self.sources,
            lambda name: self.entity.__table__.c[name],
        )
        if joined is None:
            raise TypeError(
                "Python predicates require query execution through stream()"
            )
        return apply_query(self, self.statement.where(joined))

    def join[F: SQLEntity[Any], L: SQLEntity[Any], Key: Hashable, LO, RO](
        self,
        entity: type[SQLEntity[Any, S]],
        condition: FieldComparison[L, F, Key, LO, RO],
    ) -> "SQLJoinedQuery[S, P | FieldPredicate[F], E, *Ts, F]":
        return join_query(
            self,
            entity,
            condition,
            source=self.source,
            row_conditions=self.row_conditions,
        )


def join_query[
    E: SQLEntity[Any],
    F: SQLEntity[Any],
    L: SQLEntity[Any],
    Key: Hashable,
    LO,
    RO,
    R,
    S: SQLSource,
    P: FieldPredicate,
    *Ts,
](
    query: BaseQuery[E, Select[tuple[E, *Ts]], R],
    entity: type[SQLEntity[Any, S]],
    condition: FieldComparison[L, F, Key, LO, RO],
    *,
    source: S | None,
    row_conditions: tuple[Filter[P | PredicateCallable[E]], ...],
) -> SQLJoinedQuery[S, P | FieldPredicate[F], E, *Ts, F]:
    sources = (
        query.sources if isinstance(query, SQLJoinedQuery) else (query.entity,)
    )
    if not isinstance(condition, FieldComparison):
        raise TypeError("A SQL join requires a field equality expression")
    left, right = condition.left, condition.right
    fields_match = left.entity_cls in sources and right.entity_cls is entity
    if not fields_match:
        raise TypeError("Join fields must belong to the joined entities")
    if entity in sources:
        raise TypeError("Use SQLAlchemy aliases to join the same entity twice")
    validate_source(entity)
    if entity.__signpost__ is not query.entity.__signpost__:
        raise TypeError("SQL joins require one shared signpost")
    clause = (
        left.entity_cls.__table__.c[left.name] == entity.__table__.c[right.name]
    )
    prepared = query.unfiltered().unpaged()
    prepared.orderings = ()
    return SQLJoinedQuery(
        query.entity,
        statement=prepared.build()
        .add_columns(right.entity_cls)
        .join_from(left.entity_cls, entity, clause),
        offset_value=query.offset_value,
        limit_value=query.limit_value,
        conditions=query.conditions,
        orderings=query.orderings,
        sources=(*sources, entity),
        source=source,
        row_conditions=row_conditions,
    )


def apply_query[E: SQLEntity[Any], R, *Ts](
    query: BaseQuery[E, Select[tuple[*Ts]], R],
    statement: Select[tuple[*Ts]],
) -> Select[tuple[*Ts]]:
    condition: Expression[E] = And(*query.conditions)
    predicate = compile_predicate(
        condition,
        query.entity,
        lambda name: statement.selected_columns[name],
    )
    if predicate is None:
        raise TypeError(
            "Python predicates require query execution through stream()"
        )
    statement = statement.where(predicate)
    if query.orderings:
        statement = statement.order_by(None)
    for name, reverse in query.effective_orderings:
        column = statement.selected_columns[name]
        statement = statement.order_by(
            column.desc() if reverse else column.asc()
        )
    if not isinstance(query.limit_value, UndefinedType):
        statement = statement.limit(query.limit_value)
    return statement.offset(query.offset_value or None)
