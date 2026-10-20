"""BDD phase declarations executed by pytest's fixture and test lifecycle."""

from collections.abc import AsyncIterator, Awaitable, Callable
from inspect import isasyncgenfunction, iscoroutinefunction
from typing import Literal, overload

import pytest
import pytest_asyncio

from fastsprout.core import dataclass

from .contracts import FIXTURE_CONTRACTS, StepContract, checked_signature

__all__ = ["FixtureStep", "given", "then", "when"]


@dataclass(frozen=True)
class FixtureStep:
    phase: Literal["given", "when"]
    description: str

    @overload
    def __call__[**P, R](
        self, function: Callable[P, Awaitable[R]]
    ) -> Callable[P, Awaitable[R]]: ...

    @overload
    def __call__[**P, R](
        self, function: Callable[P, AsyncIterator[R]]
    ) -> Callable[P, AsyncIterator[R]]: ...

    @overload
    def __call__[**P, R](self, function: Callable[P, R]) -> Callable[P, R]: ...

    def __call__[**P, R, T](
        self,
        function: Callable[P, R]
        | Callable[P, Awaitable[T]]
        | Callable[P, AsyncIterator[T]],
    ) -> (
        Callable[P, R]
        | Callable[P, Awaitable[T]]
        | Callable[P, AsyncIterator[T]]
    ):
        FIXTURE_CONTRACTS[function] = StepContract(
            checked_signature(function), self.description
        )
        function.__doc__ = f"{self.phase}: {self.description}"
        if iscoroutinefunction(function):
            return pytest_asyncio.fixture(function)
        if isasyncgenfunction(function):
            return pytest_asyncio.fixture(function)
        return pytest.fixture(function)


def given(description: str) -> FixtureStep:
    return FixtureStep("given", description)


def when(description: str) -> FixtureStep:
    return FixtureStep("when", description)


def then[**P, R](
    description: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        checked_signature(function)
        marked = pytest.mark.fastsprout_typed(
            phase="then", description=description
        )(function)
        return (
            pytest.mark.asyncio(marked)
            if iscoroutinefunction(function)
            else marked
        )

    return decorate
