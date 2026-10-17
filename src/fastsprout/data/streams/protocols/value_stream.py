from typing import (
    Protocol,
    runtime_checkable,
)

from fastsprout.core.types import AnyIterable, LazyAwait
from fastsprout.core.types.protocols.ables import RichComparisonable
from fastsprout.data.types import (
    ConsumerCallable,
    GetterCallable,
    MapperCallable,
    PredicateCallable,
    Valuable,
)

from .common_stream import AsyncCommonStream

__all__ = ["AsyncValueStream"]


@runtime_checkable
class AsyncValueStream[T: Valuable](AsyncCommonStream[T], Protocol):
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

    def sum(self) -> LazyAwait[T | None]: ...
