from typing import Literal

import pytest

from fastsprout.actions import DataS
from fastsprout.core import Depends
from fastsprout.testing.core import when_then

from ...common import Record, RecordCreate, RecordPatch, RecordUpdate


async def never_after_rejection() -> None:
    raise AssertionError("Dependency chain continued after rejection")


@when_then("rejected dependency stops the chain and write")
@pytest.mark.parametrize(
    "operation", ["create", "update", "entity_update", "patch"]
)
async def test_rejected_dependency_stops_the_chain_and_write(
    records: DataS[Record],
    operation: Literal["create", "update", "entity_update", "patch"],
) -> None:
    created = await records.create(Record(name="Batman"))
    calls: list[str] = []

    async def reject() -> None:
        calls.append("reject")
        raise PermissionError("Forbidden")

    service = DataS(
        Record,
        create=RecordCreate,
        update=RecordUpdate,
        patch=RecordPatch,
        dependencies=[Depends(reject), Depends(never_after_rejection)],
    )
    with pytest.raises(PermissionError, match="Forbidden"):
        if operation == "create":
            await service.create(RecordCreate(name="Robin"))
        elif operation == "update":
            await service.update(
                created.id, RecordUpdate(name="Robin", score=20)
            )
        elif operation == "entity_update":
            await service.update(created.model_copy(update={"name": "Robin"}))
        else:
            await service.patch(created.id, RecordPatch(name="Robin"))
    assert calls == ["reject"]
    found = await records.get(created.id)
    assert found is not None
    assert found.name == "Batman"
    assert await records.count() == 1
