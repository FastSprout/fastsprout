from collections.abc import AsyncIterator, Hashable
from typing import Any, Protocol, runtime_checkable

from fastsprout.core.types import AnyIterable, LazyAwait
from fastsprout.core.types.protocols.ables import RichComparisonable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import Entitieable
from fastsprout.data.types import (
    ConsumerCallable,
    GetterCallable,
    HashableAndValuable,
    MapperCallable,
    PredicateCallable,
    ReducerCallable,
)

from .value_stream import AsyncValueStream

__all__ = ["AsyncEntityStream"]


@runtime_checkable
class AsyncEntityStream[E: Entitieable](Protocol):
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

    def to_list(self) -> LazyAwait[list[E]]: ...
    def to_set(self) -> LazyAwait[set[E]]: ...
    def to_dict[K: Hashable, V](
        self,
        key: GetterCallable[E, K],
        value: GetterCallable[E, V],
    ) -> LazyAwait[dict[K, V]]: ...

    def to_values[K: HashableAndValuable](
        self, mapper: MapperCallable[E, K]
    ) -> AsyncValueStream[K]: ...
    def chunked(
        self, size: int = DEFAULT_ITERATION_CHUNK_SIZE
    ) -> AsyncIterator[list[E]]: ...
    def group_by[K: Hashable](
        self, key: GetterCallable[E, K]
    ) -> LazyAwait[dict[K, list[E]]]: ...

    def for_each(self, consumer: ConsumerCallable[E]) -> LazyAwait[None]: ...
    def reduce[R](
        self, reducer: ReducerCallable[E, R], initial: R
    ) -> LazyAwait[R]: ...
    def count(self) -> LazyAwait[int]: ...
    def first(self) -> LazyAwait[E | None]: ...
    def all(self, predicate: PredicateCallable[E]) -> LazyAwait[bool]: ...
    def any(self, predicate: PredicateCallable[E]) -> LazyAwait[bool]: ...

    def __aiter__(self) -> AsyncIterator[E]: ...
