from .base_test_simple_entity_stream import BaseTestSimpleAsyncEntityStream
from .conftest import (
    TestEntityInt,
    TestEntityStr,
    TestEntityUUID,
    build_test_entity_int,
    build_test_entity_str,
    build_test_entity_uuid,
    make_async_entity_range,
    make_entity_range,
)


class TestSimpleAsyncEntityStreamIntSync(
    BaseTestSimpleAsyncEntityStream[TestEntityInt]
):
    _entity_type = TestEntityInt
    _entity_builder = staticmethod(build_test_entity_int)
    _range_generator = staticmethod(make_entity_range)


class TestSimpleAsyncEntityStreamIntAsync(
    BaseTestSimpleAsyncEntityStream[TestEntityInt]
):
    _entity_type = TestEntityInt
    _entity_builder = staticmethod(build_test_entity_int)
    _range_generator = staticmethod(make_async_entity_range)


class TestSimpleAsyncEntityStreamStrSync(
    BaseTestSimpleAsyncEntityStream[TestEntityStr]
):
    _entity_type = TestEntityStr
    _entity_builder = staticmethod(build_test_entity_str)
    _range_generator = staticmethod(make_entity_range)


class TestSimpleAsyncEntityStreamStrAsync(
    BaseTestSimpleAsyncEntityStream[TestEntityStr]
):
    _entity_type = TestEntityStr
    _entity_builder = staticmethod(build_test_entity_str)
    _range_generator = staticmethod(make_async_entity_range)


class TestSimpleAsyncEntityStreamUUIDSync(
    BaseTestSimpleAsyncEntityStream[TestEntityUUID]
):
    _entity_type = TestEntityUUID
    _entity_builder = staticmethod(build_test_entity_uuid)
    _range_generator = staticmethod(make_entity_range)


class TestSimpleAsyncEntityStreamUUIDAsync(
    BaseTestSimpleAsyncEntityStream[TestEntityUUID]
):
    _entity_type = TestEntityUUID
    _entity_builder = staticmethod(build_test_entity_uuid)
    _range_generator = staticmethod(make_async_entity_range)
