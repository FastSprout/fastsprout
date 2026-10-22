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
    entity_type = TestEntityInt
    entity_builder = staticmethod(build_test_entity_int)
    range_generator = staticmethod(make_entity_range)


class TestSimpleAsyncEntityStreamIntAsync(
    BaseTestSimpleAsyncEntityStream[TestEntityInt]
):
    entity_type = TestEntityInt
    entity_builder = staticmethod(build_test_entity_int)
    range_generator = staticmethod(make_async_entity_range)


class TestSimpleAsyncEntityStreamStrSync(
    BaseTestSimpleAsyncEntityStream[TestEntityStr]
):
    entity_type = TestEntityStr
    entity_builder = staticmethod(build_test_entity_str)
    range_generator = staticmethod(make_entity_range)


class TestSimpleAsyncEntityStreamStrAsync(
    BaseTestSimpleAsyncEntityStream[TestEntityStr]
):
    entity_type = TestEntityStr
    entity_builder = staticmethod(build_test_entity_str)
    range_generator = staticmethod(make_async_entity_range)


class TestSimpleAsyncEntityStreamUUIDSync(
    BaseTestSimpleAsyncEntityStream[TestEntityUUID]
):
    entity_type = TestEntityUUID
    entity_builder = staticmethod(build_test_entity_uuid)
    range_generator = staticmethod(make_entity_range)


class TestSimpleAsyncEntityStreamUUIDAsync(
    BaseTestSimpleAsyncEntityStream[TestEntityUUID]
):
    entity_type = TestEntityUUID
    entity_builder = staticmethod(build_test_entity_uuid)
    range_generator = staticmethod(make_async_entity_range)
