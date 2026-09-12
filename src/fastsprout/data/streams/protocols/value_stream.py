from collections.abc import AsyncIterator, Hashable
from typing import (
    Protocol,
    runtime_checkable,
)

from fastsprout.core.types import AnyIterable, LazyAwait
from fastsprout.core.types.protocols.ables import Addable, RichComparisonable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.types import (
    ConsumerCallable,
    GetterCallable,
    MapperCallable,
    PredicateCallable,
    ReducerCallable,
    Valuable,
)

__all__ = ["AsyncValueStream"]


@runtime_checkable
class AsyncValueStream[T: Valuable](Protocol):
    def concat(
        self, *others: "AsyncValueStream[T] | AnyIterable[T]"
    ) -> "AsyncValueStream[T]": ...

    def sort[R: RichComparisonable](
        self,
        key: GetterCallable[T, R] | None = None,
        reverse: bool = False,
    ) -> "AsyncValueStream[T]": ...

    def map[R: Valuable](
        self, mapper: MapperCallable[T, R]
    ) -> "AsyncValueStream[R]": ...

    def filter(
        self, predicate: PredicateCallable[T]
    ) -> "AsyncValueStream[T]": ...
    def distinct(self) -> "AsyncValueStream[T]": ...
    def peek(self, consumer: ConsumerCallable[T]) -> "AsyncValueStream[T]": ...

    def take(self, n: int) -> "AsyncValueStream[T]": ...
    def drop(self, n: int) -> "AsyncValueStream[T]": ...
    def take_while(
        self, predicate: PredicateCallable[T]
    ) -> "AsyncValueStream[T]": ...
    def drop_while(
        self, predicate: PredicateCallable[T]
    ) -> "AsyncValueStream[T]": ...

    def to_list(self) -> LazyAwait[list[T]]: ...
    def to_set(self) -> LazyAwait[set[T]]: ...
    def to_dict[K: Hashable, V](
        self,
        key: GetterCallable[T, K],
        value: GetterCallable[T, V],
    ) -> LazyAwait[dict[K, V]]: ...
    def chunked(
        self, size: int = DEFAULT_ITERATION_CHUNK_SIZE
    ) -> AsyncIterator[list[T]]: ...
    def group_by[K: Hashable](
        self, key: GetterCallable[T, K]
    ) -> LazyAwait[dict[K, list[T]]]: ...

    def for_each(self, consumer: ConsumerCallable[T]) -> LazyAwait[None]: ...
    def reduce[R](
        self, reducer: ReducerCallable[T, R], initial: R
    ) -> LazyAwait[R]: ...
    def count(self) -> LazyAwait[int]: ...
    def first(self) -> LazyAwait[T | None]: ...
    def all(self, predicate: PredicateCallable[T]) -> LazyAwait[bool]: ...
    def any(self, predicate: PredicateCallable[T]) -> LazyAwait[bool]: ...

    def sum_by[R: Addable](
        self, key: GetterCallable[T, R]
    ) -> LazyAwait[R | None]: ...

    def sum(self) -> LazyAwait[T | None]: ...

    def min[K: RichComparisonable](
        self, key: GetterCallable[T, K]
    ) -> LazyAwait[T | None]: ...

    def max[K: RichComparisonable](
        self, key: GetterCallable[T, K]
    ) -> LazyAwait[T | None]: ...

    def __aiter__(self) -> AsyncIterator[T]: ...
