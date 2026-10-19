from typing import Literal

import pytest

from fastsprout.actions import DataS, WriteOperation
from fastsprout.core import Depends
from fastsprout.data import DataR
from fastsprout.testing.core import when_then

from ...common import (
    Record,
    RecordCreate,
    RecordPatch,
    RecordUpdate,
    RecordValidation,
)


@when_then(
    "validation failure stops later dependencies and prevents persistence"
)
@pytest.mark.parametrize(
    "write, operation",
    [
        ("create", "create"),
        ("update", "update"),
        ("entity_update", "update"),
        ("patch", "patch"),
    ],
)
async def test_validation_failure_prevents_persistence(
    records: DataS[Record],
    write: Literal["create", "update", "entity_update", "patch"],
    operation: WriteOperation,
) -> None:
    def after_validation() -> None:
        raise AssertionError("Dependency chain continued after rejection")

    validation = RecordValidation()
    service = DataS(
        Record,
        create=RecordCreate,
        update=RecordUpdate,
        patch=RecordPatch,
        dependencies=[Depends(validation), Depends(after_validation)],
    )
    async with DataR() as datar:
        created = await records.create(
            Record(name="Batman", score=42), datar=datar
        )
        with pytest.raises(ValueError, match="non-negative"):
            if write == "create":
                await service.create(
                    RecordCreate(name="Robin", score=-1), datar=datar
                )
            elif write == "update":
                await service.update(
                    created.id,
                    RecordUpdate(name="Robin", score=-1),
                    datar=datar,
                )
            elif write == "patch":
                await service.patch(
                    created.id, RecordPatch(score=-1), datar=datar
                )
            else:
                await service.update(
                    created.model_copy(update={"score": -1}), datar=datar
                )
        assert len(validation.calls) == 1
        assert validation.calls[0][0] == operation
        found = await records.get(created.id, datar=datar)
        assert found is not None
        assert (found.name, found.score) == ("Batman", 42)
        assert await records.count(datar=datar) == 1


@when_then("validation receives action inputs and the same context")
async def test_validation_receives_action_inputs_and_the_same_context(
    records: DataS[Record],
) -> None:
    validation = RecordValidation()
    service = DataS(
        Record,
        create=RecordCreate,
        patch=RecordPatch,
        dependencies=[Depends(validation)],
    )
    async with DataR() as datar:
        created = await service.create(
            RecordCreate(name="  Batman  "), datar=datar
        )
        with pytest.raises(ValueError, match="non-negative"):
            await service.patch(created.id, RecordPatch(score=-1), datar=datar)
    assert created.name == "Batman"
    assert validation.calls == [
        ("create", datar, frozenset({"name"})),
        ("patch", datar, frozenset({"score"})),
    ]


class ValidatedRecords(DataS[Record]):
    dependencies = (Depends(RecordValidation()),)


@when_then("replacing dependencies preserves the inherited validator")
async def test_validation_can_be_inherited_and_replaced(
    records: DataS[Record],
) -> None:
    service = ValidatedRecords()
    original = service.dependencies[0].dependency
    assert isinstance(original, RecordValidation)
    async with DataR() as datar:
        with pytest.raises(ValueError, match="non-negative"):
            await service.create(Record(name="Batman", score=-1), datar=datar)
        replacement = RecordValidation()
        service = ValidatedRecords(dependencies=[Depends(replacement)])
        await service.create(Record(name="Batman", score=10), datar=datar)
    assert len(replacement.calls) == 1
    assert len(original.calls) == 1
    assert service.dependencies[0].dependency is replacement


@when_then("validation hook normalizes input")
async def test_validation_hook_normalizes_input(
    records: DataS[Record],
) -> None:
    def rename(entity: Record) -> None:
        entity.name = "Robin"

    service = DataS(Record, dependencies=[Depends(rename)])
    async with DataR() as datar:
        created = await service.create(Record(name="Batman"), datar=datar)
        assert created.name == "Robin"
        found = await records.get(created.id, datar=datar)
        assert found is not None
        assert found.name == "Robin"
