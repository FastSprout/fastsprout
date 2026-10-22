from collections.abc import AsyncIterable
from typing import (
    Protocol,
    runtime_checkable,
)

from fastsprout.core.types import AnyIterable, LazyAwait
from fastsprout.core.types.protocols.ables import Addable, RichComparisonable
from fastsprout.data.types import (
    ConsumerCallable,
    GetterCallable,
    MapperCallable,
    PredicateCallable,
    Valuable,
)

from .common_stream import AsyncCommonStreamable

__all__ = ["AsyncValueStreamable"]


@runtime_checkable
class AsyncValueStreamable[T: Valuable](AsyncCommonStreamable[T], Protocol):
    def concat(
        self, *others: "AsyncValueStreamable[T] | AnyIterable[T]"
    ) -> "AsyncValueStreamable[T]": ...

    def sort[R: RichComparisonable](
        self,
        key: GetterCallable[T, R] | None = None,
        reverse: bool = False,
    ) -> "AsyncValueStreamable[T]": ...

    def map[R: Valuable](
        self, mapper: MapperCallable[T, R]
    ) -> "AsyncValueStreamable[R]": ...

    def filter(
        self, predicate: PredicateCallable[T]
    ) -> "AsyncValueStreamable[T]": ...
    def distinct(self) -> "AsyncValueStreamable[T]": ...
    def peek(
        self, consumer: ConsumerCallable[T]
    ) -> "AsyncValueStreamable[T]": ...

    def take(self, n: int) -> "AsyncValueStreamable[T]": ...
    def drop(self, n: int) -> "AsyncValueStreamable[T]": ...
    def take_while(
        self, predicate: PredicateCallable[T]
    ) -> "AsyncValueStreamable[T]": ...
    def drop_while(
        self, predicate: PredicateCallable[T]
    ) -> "AsyncValueStreamable[T]": ...

    def sum[R: Valuable](
        self: AsyncIterable[Addable[T, R]],
    ) -> LazyAwait[T | R | None]: ...
