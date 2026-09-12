from fastsprout.core import Depends
from fastsprout.data.unit_of_work.implementation import SimpleUnitOfWork

__all__ = [
    "TestObject",
    "TestObjectWithArgs",
    "TestUnitOfWork",
    "TestUnitOfWorkWithArgs",
]


class TestObject:
    __test__ = False
    pass


class TestUnitOfWork(SimpleUnitOfWork):
    __test__ = False
    test: TestObject = Depends()


class TestObjectWithArgs:
    __test__ = False

    def __init__(self, value: int) -> None:
        self.value = value


class TestUnitOfWorkWithArgs(SimpleUnitOfWork):
    __test__ = False

    test: TestObjectWithArgs = Depends()
