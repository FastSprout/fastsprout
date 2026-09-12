from typing import Any

import pytest

from fastsprout.core.types import AnyIterable
from fastsprout.data.utils.iterable import achain, resolve_any_iterable
from tests.fastsprout.data.conftest import ANY_ITERABLES


@pytest.mark.parametrize(
    "iterable",
    ANY_ITERABLES,
)
async def test_resolve_any_iterable(iterable: AnyIterable[Any]):
    # given
    # when
    aiterable = resolve_any_iterable(iterable)
    # then
    async for _ in aiterable:
        pass


async def test_achain(any_iterables):
    # given
    # when
    aiterable = achain(*any_iterables)
    # then
    async for _ in aiterable:
        pass
