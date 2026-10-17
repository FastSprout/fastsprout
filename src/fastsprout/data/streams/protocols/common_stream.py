from collections.abc import AsyncIterator, Hashable
from typing import Protocol, runtime_checkable

from fastsprout.core.types import LazyAwait
from fastsprout.core.types.protocols.ables import Addable, RichComparisonable
from fastsprout.data.consts import DEFAULT_ITERATION_CHUNK_SIZE
from fastsprout.data.entity import Entitieable
from fastsprout.data.types import (
    ConsumerCallable,
    GetterCallable,
    PredicateCallable,
    ReducerCallable,
    Valuable,
)

__all__ = ["AsyncCommonStream"]


@runtime_checkable
class AsyncCommonStream[T: Valuable | Entitieable](Protocol):
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

    def min[K: RichComparisonable](
        self, key: GetterCallable[T, K]
    ) -> LazyAwait[T | None]: ...

    def max[K: RichComparisonable](
        self, key: GetterCallable[T, K]
    ) -> LazyAwait[T | None]: ...

    def __aiter__(self) -> AsyncIterator[T]: ...
