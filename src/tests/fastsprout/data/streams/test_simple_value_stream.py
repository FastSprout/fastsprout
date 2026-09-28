from decimal import Decimal

from .base_test_simple_value_stream import BaseTestSimpleAsyncValueStream
from .conftest import make_async_range, make_range


class TestSimpleAsyncValueStreamIntSync(BaseTestSimpleAsyncValueStream):
    _type: type[int] = int
    _range_generator = staticmethod(make_range)


class TestSimpleAsyncValueStreamIntAsync(BaseTestSimpleAsyncValueStream):
    _type: type[int] = int
    _range_generator = staticmethod(make_async_range)


class TestSimpleAsyncValueStreamFloatSync(BaseTestSimpleAsyncValueStream):
    _type: type[float] = float
    _range_generator = staticmethod(make_range)


class TestSimpleAsyncValueStreamFloatAsync(BaseTestSimpleAsyncValueStream):
    _type: type[float] = float
    _range_generator = staticmethod(make_async_range)


class TestSimpleAsyncValueStreamDecimalSync(
    BaseTestSimpleAsyncValueStream[Decimal]
):
    _type: type[Decimal] = Decimal
    _range_generator = staticmethod(make_range)


class TestSimpleAsyncValueStreamDecimalAsync(
    BaseTestSimpleAsyncValueStream[Decimal]
):
    _type: type[Decimal] = Decimal
    _range_generator = staticmethod(make_async_range)


class TestSimpleAsyncValueStreamStrSync(BaseTestSimpleAsyncValueStream[str]):
    _type: type[str] = str
    _range_generator = staticmethod(make_range)


class TestSimpleAsyncValueStreamStrAsync(BaseTestSimpleAsyncValueStream[str]):
    _type: type[str] = str
    _range_generator = staticmethod(make_async_range)
