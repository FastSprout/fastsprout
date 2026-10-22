from decimal import Decimal
from itertools import chain
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from fastsprout.data.streams.implementation import SimpleAsyncValueStream
from fastsprout.data.utils.iterable import resolve_any_iterable
from fastsprout.testing.core import given, then, when
from tests.type_checking import TypeChecker

from .base_test_simple_value_stream import BaseTestSimpleAsyncValueStream
from .conftest import make_async_range, make_range


class TestSimpleAsyncValueStreamIntSync(BaseTestSimpleAsyncValueStream):
    value_type: type[int] = int
    range_generator = staticmethod(make_range)


class TestSimpleAsyncValueStreamIntAsync(BaseTestSimpleAsyncValueStream):
    value_type: type[int] = int
    range_generator = staticmethod(make_async_range)


class TestSimpleAsyncValueStreamFloatSync(BaseTestSimpleAsyncValueStream):
    value_type: type[float] = float
    range_generator = staticmethod(make_range)


class TestSimpleAsyncValueStreamFloatAsync(BaseTestSimpleAsyncValueStream):
    value_type: type[float] = float
    range_generator = staticmethod(make_async_range)


class TestSimpleAsyncValueStreamDecimalSync(
    BaseTestSimpleAsyncValueStream[Decimal]
):
    value_type: type[Decimal] = Decimal
    range_generator = staticmethod(make_range)


class TestSimpleAsyncValueStreamDecimalAsync(
    BaseTestSimpleAsyncValueStream[Decimal]
):
    value_type: type[Decimal] = Decimal
    range_generator = staticmethod(make_async_range)


class TestSimpleAsyncValueStreamStrSync(BaseTestSimpleAsyncValueStream[str]):
    value_type: type[str] = str
    range_generator = staticmethod(make_range)


class TestSimpleAsyncValueStreamStrAsync(BaseTestSimpleAsyncValueStream[str]):
    value_type: type[str] = str
    range_generator = staticmethod(make_async_range)


class TestTupleSum:
    @given("fixed-length tuples from a synchronous or asynchronous source")
    def tuple_stream(
        self, values: list[tuple[int, str]], asynchronous: bool
    ) -> SimpleAsyncValueStream[tuple[int, str]]:
        return SimpleAsyncValueStream(
            resolve_any_iterable(values) if asynchronous else values
        )

    @when("the tuple stream is summed")
    async def total(
        self, tuple_stream: SimpleAsyncValueStream[tuple[int, str]]
    ) -> tuple[int | str, ...] | None:
        return await tuple_stream.sum()

    @pytest.mark.parametrize("asynchronous", [False, True])
    @pytest.mark.parametrize("values", [[], [(1, "a")], [(1, "a"), (2, "b")]])
    @then("concatenation preserves each element and permits a longer tuple")
    def test_sum(
        self, values: list[tuple[int, str]], total: tuple[int | str, ...] | None
    ) -> None:
        expected = tuple(chain.from_iterable(values)) if values else None
        assert total == expected


class TestValueSumTyping:
    @given("sum calls for scalar values and heterogeneous tuples")
    def source(self) -> Path:
        return Path(__file__).with_name("value_sum_typing.py.txt")

    @when("the sum result types are checked")
    def checked(
        self, source: Path, type_checker: TypeChecker
    ) -> CompletedProcess[str]:
        return type_checker.run(source)

    @then("scalar types remain exact and tuple results allow concatenation")
    def test_types(
        self,
        source: Path,
        type_checker: TypeChecker,
        checked: CompletedProcess[str],
    ) -> None:
        type_checker.verify(source, checked)
