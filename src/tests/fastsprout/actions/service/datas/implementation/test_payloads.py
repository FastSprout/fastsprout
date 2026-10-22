from fastsprout.actions.service.datas.implementation.payloads import materialize
from fastsprout.core import Field, dataclass
from fastsprout.data import DataR
from fastsprout.testing.core import given, then, when

from ..common import MemoryRecord


@dataclass(kw_only=True)
class CyclicRecord(MemoryRecord):
    parent: Field["CyclicRecord | None"] = Field(default=None)


class TestPayloadRelations:
    @given("a persisted entity whose relationship points to itself")
    def cyclic(self) -> CyclicRecord:
        entity = CyclicRecord(name="cycle")
        entity.parent = entity
        return entity

    @when("the cyclic relationship is prepared for an update")
    async def rejected(self, cyclic: CyclicRecord) -> ValueError | None:
        try:
            await materialize(
                CyclicRecord, cyclic, DataR(), creating=False, stored=cyclic
            )
        except ValueError as error:
            return error
        return None

    @then("cycles fail explicitly instead of recursing indefinitely")
    def test_cycle(self, rejected: ValueError | None) -> None:
        assert isinstance(rejected, ValueError)
        assert str(rejected) == "Cyclic CRUD payload"
