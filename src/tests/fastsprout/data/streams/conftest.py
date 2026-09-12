import random
from collections.abc import AsyncIterable, Callable
from typing import Any
from uuid import uuid4

from fastsprout.core import IdentificatorType
from fastsprout.data.entity import BaseEntity

__all__ = [
    "RANGE_START_END",
    "TestEntityInt",
    "TestEntityStr",
    "TestEntityUUID",
    "build_test_entity_int",
    "build_test_entity_str",
    "build_test_entity_uuid",
    "make_async_entity_range",
    "make_async_range",
    "make_entity_range",
    "make_range",
]

RANGE_START_END = (0, 10)


def make_range[T, R](
    type: Callable[[type[T]], R],
    start=RANGE_START_END[0],
    end=RANGE_START_END[1],
):
    return map(type, range(start, end))  # pyright: ignore[reportArgumentType]


def make_async_range[T, R](
    type: Callable[[type[T]], R],
    start=RANGE_START_END[0],
    end=RANGE_START_END[1],
):
    async def wrapper() -> AsyncIterable[R]:
        for item in map(type, range(start, end)):  # pyright: ignore[reportArgumentType]
            yield item

    return wrapper()


class TestEntityInt(BaseEntity[int]):
    __test__ = False


class TestEntityStr(BaseEntity[str]):
    __test__ = False


class TestEntityUUID(BaseEntity[IdentificatorType]):
    __test__ = False


def build_test_entity_int() -> TestEntityInt:
    return TestEntityInt(id=random.randint(1, 1_000_000))


def build_test_entity_str() -> TestEntityStr:
    return TestEntityStr(id=str(random.randint(1, 1_000_000)))


def build_test_entity_uuid() -> TestEntityUUID:
    return TestEntityUUID(id=uuid4())


def make_entity_range[E: BaseEntity[Any]](
    builder: Callable[[], E] = build_test_entity_int,
    start=RANGE_START_END[0],
    end=RANGE_START_END[1],
):
    return (builder() for _ in range(start, end))


def make_async_entity_range[E: BaseEntity[Any]](
    builder: Callable[[], E] = build_test_entity_int,
    start=RANGE_START_END[0],
    end=RANGE_START_END[1],
):
    async def wrapper() -> AsyncIterable[E]:
        for _ in range(start, end):
            yield builder()

    return wrapper()
