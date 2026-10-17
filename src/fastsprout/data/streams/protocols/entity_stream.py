from typing import Any, Protocol, runtime_checkable

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

from .common_stream import AsyncCommonStream
from .value_stream import AsyncValueStream

__all__ = ["AsyncEntityStream"]


@runtime_checkable
class AsyncEntityStream[E: Entitieable](AsyncCommonStream[E], Protocol):
    """Composable async stream of entities.

    Transformations are lazy. Terminal operations materialize results.
    Use `map_to_stream(key)` to extract values and exit the entity-stream.
    """

    def concat(
        self, *others: "AsyncEntityStream[E] | AnyIterable[E]"
    ) -> "AsyncEntityStream[E]": ...

    def map[R: Entitieable](
        self, mapper: MapperCallable[E, R]
    ) -> "AsyncEntityStream[R]": ...

    def sort[R: RichComparisonable[Any]](
        self, key: GetterCallable[E, R], reverse: bool = False
    ) -> "AsyncEntityStream[E]": ...
    def filter(
        self, predicate: PredicateCallable[E]
    ) -> "AsyncEntityStream[E]": ...
    def only_of[R: Entitieable[Any]](
        self, entity: type[R]
    ) -> "AsyncEntityStream[R]":
        """Narrow to one entity type — pull subtypes out of a mixed
        stream. One pass per consumption: to take several views without
        re-reading the source, materialize first (`to_list`), then
        split the list."""
        ...

    def distinct(self) -> "AsyncEntityStream[E]": ...
    def peek(self, consumer: ConsumerCallable[E]) -> "AsyncEntityStream[E]": ...

    # Slicing
    def take(self, n: int) -> "AsyncEntityStream[E]": ...
    def drop(self, n: int) -> "AsyncEntityStream[E]": ...
    def take_while(
        self, predicate: PredicateCallable[E]
    ) -> "AsyncEntityStream[E]": ...
    def drop_while(
        self, predicate: PredicateCallable[E]
    ) -> "AsyncEntityStream[E]": ...

    def to_values[K: HashableAndValuable](
        self, mapper: MapperCallable[E, K]
    ) -> AsyncValueStream[K]: ...
