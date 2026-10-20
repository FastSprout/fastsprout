from collections.abc import Awaitable, Callable
from typing import Literal

import pytest

from fastsprout.actions import DataS
from fastsprout.core import Depends
from fastsprout.testing.core import then, when

from ...common import Record, RecordCreate, RecordPatch, RecordUpdate


async def never_after_rejection() -> None:
    raise AssertionError("Dependency chain continued after rejection")


@when("one of the write operations encounters a rejecting dependency")
async def rejected_attempt(
    records: DataS[Record],
    operation: Literal["create", "update", "entity_update", "patch"],
) -> tuple[Record, list[str], PermissionError | None]:
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
    writes: dict[
        Literal["create", "update", "entity_update", "patch"],
        Callable[[], Awaitable[Record]],
    ] = {
        "create": lambda: service.create(RecordCreate(name="Robin")),
        "update": lambda: service.update(
            created.id, RecordUpdate(name="Robin", score=20)
        ),
        "entity_update": lambda: service.update(
            created.model_copy(update={"name": "Robin"})
        ),
        "patch": lambda: service.patch(created.id, RecordPatch(name="Robin")),
    }
    failure = None
    try:
        await writes[operation]()
    except PermissionError as error:
        failure = error
    return created, calls, failure


@then("rejected dependency stops the chain and write")
@pytest.mark.parametrize(
    "operation", ["create", "update", "entity_update", "patch"]
)
async def test_rejected_dependency_stops_the_chain_and_write(
    records: DataS[Record],
    rejected_attempt: tuple[Record, list[str], PermissionError | None],
) -> None:
    created, calls, failure = rejected_attempt
    assert isinstance(failure, PermissionError)
    assert str(failure) == "Forbidden"
    assert calls == ["reject"]
    found = await records.get(created.id)
    assert found is not None
    assert found.name == "Batman"
    assert await records.count() == 1
