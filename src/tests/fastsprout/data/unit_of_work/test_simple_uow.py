from random import randint

from .base_test_simple_uow import BaseTestUnitOfWork
from .conftest import (
    TestObject,
    TestObjectWithArgs,
    TestUnitOfWork,
    TestUnitOfWorkWithArgs,
)


class TestSimpleUnitOfWork(BaseTestUnitOfWork[TestUnitOfWork]):
    _uow_type = TestUnitOfWork
    _attr_name = "test"
    _attr_type = TestObject
    _args = staticmethod(tuple)
    _kwargs = staticmethod(dict)


class TestSimpleUnitOfWorkWithArgs(BaseTestUnitOfWork[TestUnitOfWorkWithArgs]):
    _uow_type = TestUnitOfWorkWithArgs
    _attr_name = "test"
    _attr_type = TestObjectWithArgs
    _args = staticmethod(lambda: (randint(0, 1_000_000),))
    _kwargs = staticmethod(dict)
