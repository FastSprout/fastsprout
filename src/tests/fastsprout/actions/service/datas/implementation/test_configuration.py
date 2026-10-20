import pytest

from fastsprout.actions import DataS
from fastsprout.core import Depends
from fastsprout.data import DataR
from fastsprout.data.capabilities.query import BaseQuery

from ..common import Record


class FixedCount(DataS[Record]):
    async def count[Statement](
        self,
        query: BaseQuery[Record, Statement] | None = None,
        *,
        datar: DataR = Depends(),
    ) -> int:
        return 99


class TestOperationControls:
    async def test_switches_guard_overridden_actions(self) -> None:
        # given
        service = FixedCount(operations=frozenset({"get", "count"}))
        # then
        assert await service.count() == 99
        with pytest.raises(AttributeError, match="disabled"):
            await service.create(Record(name="Batman"))
        service.operations = frozenset({"get"})
        with pytest.raises(AttributeError, match="disabled"):
            await service.count()
        service.operations = frozenset({"count"})
        assert await service.count() == 99
