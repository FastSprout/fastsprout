from collections.abc import Awaitable, Callable
from typing import Literal

import pytest

from fastsprout.actions import DataS, WriteOperation
from fastsprout.core import Depends
from fastsprout.data import DataR
from fastsprout.testing.core import then, when

from ...common import (
    Record,
    RecordCreate,
    RecordPatch,
    RecordUpdate,
    RecordValidation,
)


@when("a write payload is rejected by validation")
async def rejected_write(
    records: DataS[Record],
    write: Literal["create", "update", "entity_update", "patch"],
    active_datar: DataR,
) -> tuple[RecordValidation, Record, ValueError | None]:
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
    datar = active_datar
    created = await records.create(Record(name="Batman", score=42), datar=datar)
    writes: dict[
        Literal["create", "update", "entity_update", "patch"],
        Callable[[], Awaitable[Record]],
    ] = {
        "create": lambda: service.create(
            RecordCreate(name="Robin", score=-1), datar=datar
        ),
        "update": lambda: service.update(
            created.id, RecordUpdate(name="Robin", score=-1), datar=datar
        ),
        "patch": lambda: service.patch(
            created.id, RecordPatch(score=-1), datar=datar
        ),
        "entity_update": lambda: service.update(
            created.model_copy(update={"score": -1}), datar=datar
        ),
    }
    failure = None
    try:
        await writes[write]()
    except ValueError as error:
        failure = error
    return validation, created, failure


@then("validation failure stops later dependencies and prevents persistence")
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
    active_datar: DataR,
    operation: WriteOperation,
    rejected_write: tuple[RecordValidation, Record, ValueError | None],
) -> None:
    validation, created, failure = rejected_write
    assert isinstance(failure, ValueError)
    assert "non-negative" in str(failure)
    assert len(validation.calls) == 1
    assert validation.calls[0][0] == operation
    found = await records.get(created.id, datar=active_datar)
    assert found is not None
    assert (found.name, found.score) == ("Batman", 42)
    assert await records.count(datar=active_datar) == 1


@when("a normalizable create is followed by an invalid patch")
async def contextual_validation(
    active_datar: DataR,
) -> tuple[RecordValidation, Record, ValueError | None]:
    validation = RecordValidation()
    service = DataS(
        Record,
        create=RecordCreate,
        patch=RecordPatch,
        dependencies=[Depends(validation)],
    )
    created = await service.create(
        RecordCreate(name="  Batman  "), datar=active_datar
    )
    failure = None
    try:
        await service.patch(
            created.id, RecordPatch(score=-1), datar=active_datar
        )
    except ValueError as error:
        failure = error
    return validation, created, failure


@then("validation receives action inputs and the same context")
def test_validation_receives_action_inputs_and_the_same_context(
    active_datar: DataR,
    contextual_validation: tuple[RecordValidation, Record, ValueError | None],
) -> None:
    validation, created, failure = contextual_validation
    assert isinstance(failure, ValueError)
    assert "non-negative" in str(failure)
    assert created.name == "Batman"
    assert validation.calls == [
        ("create", active_datar, frozenset({"name"})),
        ("patch", active_datar, frozenset({"score"})),
    ]


class ValidatedRecords(DataS[Record]):
    dependencies = (Depends(RecordValidation()),)


@when("a validator is inherited and then overridden for one instance")
async def replaced_validation(
    active_datar: DataR,
) -> tuple[
    RecordValidation, RecordValidation, ValidatedRecords, ValueError | None
]:
    service = ValidatedRecords()
    original = service.dependencies[0].dependency
    assert isinstance(original, RecordValidation)
    failure = None
    try:
        await service.create(
            Record(name="Batman", score=-1), datar=active_datar
        )
    except ValueError as error:
        failure = error
    replacement = RecordValidation()
    service = ValidatedRecords(dependencies=[Depends(replacement)])
    await service.create(Record(name="Batman", score=10), datar=active_datar)
    return original, replacement, service, failure


@then("replacing dependencies preserves the inherited validator")
def test_validation_can_be_inherited_and_replaced(
    replaced_validation: tuple[
        RecordValidation, RecordValidation, ValidatedRecords, ValueError | None
    ],
) -> None:
    original, replacement, service, failure = replaced_validation
    assert isinstance(failure, ValueError)
    assert "non-negative" in str(failure)
    assert len(replacement.calls) == 1
    assert len(original.calls) == 1
    assert service.dependencies[0].dependency is replacement


@when("a dependency renames an entity before creation")
async def renamed_record(active_datar: DataR) -> Record:
    def rename(entity: Record) -> None:
        entity.name = "Robin"

    service = DataS(Record, dependencies=[Depends(rename)])
    return await service.create(Record(name="Batman"), datar=active_datar)


@then("validation hook normalizes input")
async def test_validation_hook_normalizes_input(
    records: DataS[Record], active_datar: DataR, renamed_record: Record
) -> None:
    assert renamed_record.name == "Robin"
    found = await records.get(renamed_record.id, datar=active_datar)
    assert found is not None
    assert found.name == "Robin"
