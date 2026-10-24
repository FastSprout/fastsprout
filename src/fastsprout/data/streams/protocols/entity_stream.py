from abc import abstractmethod
from collections.abc import Hashable
from typing import Any, Protocol, runtime_checkable

from fastsprout.core.fields.field_ref import FieldRef
from fastsprout.core.types import AnyIterable
from fastsprout.core.types.protocols.ables import RichComparisonable
from fastsprout.data.entity import Entitieable
from fastsprout.data.types import (
    ConsumerCallable,
    GetterCallable,
    HashableAndValuable,
    MapperCallable,
    PredicateCallable,
)

from .common_stream import AsyncCommonStreamable
from .joined_stream import AsyncJoinedStreamable
from .value_stream import AsyncValueStreamable

__all__ = ["AsyncEntityStreamable"]


@runtime_checkable
class AsyncEntityStreamable[E: Entitieable](AsyncCommonStreamable[E], Protocol):
    """Composable async stream of entities.

    Transformations are lazy. Terminal operations materialize results.
    Use `map_to_stream(key)` to extract values and exit the entity-stream.
    """

    def join[F: Entitieable, Key: Hashable, LeftOrm, RightOrm](
        self,
        other: "AsyncEntityStreamable[F]",
        *,
        on: tuple[FieldRef[E, Key, LeftOrm], FieldRef[F, Key, RightOrm]],
    ) -> AsyncJoinedStreamable[E, F]: ...

    def concat(
        self, *others: "AsyncEntityStreamable[E] | AnyIterable[E]"
    ) -> "AsyncEntityStreamable[E]": ...

    def map[R: Entitieable](
        self, mapper: MapperCallable[E, R]
    ) -> "AsyncEntityStreamable[R]": ...

    def sort[R: RichComparisonable[Any]](
        self, key: GetterCallable[E, R], reverse: bool = False
    ) -> "AsyncEntityStreamable[E]": ...
    def filter(
        self, predicate: PredicateCallable[E]
    ) -> "AsyncEntityStreamable[E]": ...
    @abstractmethod
    def only_of[R: Entitieable](
        self, entity: type[R]
    ) -> "AsyncEntityStreamable[R]":
        """Narrow to one entity type — pull subtypes out of a mixed
        stream. One pass per consumption: to take several views without
        re-reading the source, materialize first (`to_list`), then
        split the list."""

    def distinct(self) -> "AsyncEntityStreamable[E]": ...
    def peek(
        self, consumer: ConsumerCallable[E]
    ) -> "AsyncEntityStreamable[E]": ...

    # Slicing
    def take(self, n: int) -> "AsyncEntityStreamable[E]": ...
    def drop(self, n: int) -> "AsyncEntityStreamable[E]": ...
    def take_while(
        self, predicate: PredicateCallable[E]
    ) -> "AsyncEntityStreamable[E]": ...
    def drop_while(
        self, predicate: PredicateCallable[E]
    ) -> "AsyncEntityStreamable[E]": ...

    def to_values[K: HashableAndValuable](
        self, mapper: MapperCallable[E, K]
    ) -> AsyncValueStreamable[K]: ...
