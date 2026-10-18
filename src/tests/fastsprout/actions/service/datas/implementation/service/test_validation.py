from collections.abc import Sequence
from typing import Literal
from uuid import uuid4

import pytest

from fastsprout.actions import DataS, WriteOperation
from fastsprout.core import Depends
from fastsprout.core.depends import DependsClass
from fastsprout.data import DataR

from ...common import (
    Record,
    RecordCreate,
    RecordPatch,
    RecordUpdate,
    RecordValidation,
)


class ValidatedRecords(DataS[Record]):
    dependencies: Sequence[DependsClass] = (Depends(RecordValidation()),)


class TestValidation:
    async def test_exists_checks_the_key_before_and_after_delete(
        self,
        records: DataS[Record],
    ) -> None:
        # given
        # when / then
        async with DataR() as datar:
            assert await records.exists(uuid4(), datar=datar) is False
            created = await records.create(Record(name="Batman"), datar=datar)
            assert await records.exists(created.id, datar=datar) is True
            await records.delete(created.id, datar=datar)
            assert await records.exists(created.id, datar=datar) is False

    async def test_exists_has_an_independent_operation_switch(
        self,
        records: DataS[Record],
    ) -> None:
        # given
        operations: list[str] = []

        def observe(operation: str) -> None:
            operations.append(operation)

        service = DataS(
            Record,
            dependencies=[Depends(observe)],
            operations=frozenset({"exists"}),
        )
        # when / then
        async with DataR() as datar:
            created = await records.create(Record(name="Batman"), datar=datar)
            assert await service.exists(created.id, datar=datar) is True
            service.operations = frozenset()
            with pytest.raises(AttributeError, match="disabled"):
                await service.exists(created.id, datar=datar)
        assert operations == ["exists"]

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
        self,
        records: DataS[Record],
        write: Literal["create", "update", "entity_update", "patch"],
        operation: WriteOperation,
    ) -> None:
        # given
        validation = RecordValidation()
        service = DataS(
            Record,
            create=RecordCreate,
            update=RecordUpdate,
            patch=RecordPatch,
            dependencies=[Depends(validation)],
        )
        # when / then
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

    async def test_validation_receives_action_inputs_and_the_same_context(
        self,
        records: DataS[Record],
    ) -> None:
        # given
        validation = RecordValidation()
        service = DataS(
            Record,
            create=RecordCreate,
            patch=RecordPatch,
            dependencies=[Depends(validation)],
        )
        # when / then
        async with DataR() as datar:
            created = await service.create(
                RecordCreate(name="  Batman  "), datar=datar
            )
            with pytest.raises(ValueError, match="non-negative"):
                await service.patch(
                    created.id, RecordPatch(score=-1), datar=datar
                )
        assert created.name == "Batman"
        assert validation.calls == [
            ("create", datar, frozenset({"name"})),
            ("patch", datar, frozenset({"score"})),
        ]

    async def test_validation_can_be_inherited_and_replaced(
        self,
        records: DataS[Record],
    ) -> None:
        # given
        service = ValidatedRecords()
        original = service.dependencies[0].dependency
        assert isinstance(original, RecordValidation)
        # when / then
        async with DataR() as datar:
            with pytest.raises(ValueError, match="non-negative"):
                await service.create(
                    Record(name="Batman", score=-1), datar=datar
                )
            replacement = RecordValidation()
            service = ValidatedRecords(dependencies=[Depends(replacement)])
            await service.create(Record(name="Batman", score=10), datar=datar)
        assert service.dependencies[0].dependency is replacement
        assert len(replacement.calls) == 1
        assert len(original.calls) == 1

    async def test_validation_hook_normalizes_input(
        self,
        records: DataS[Record],
    ) -> None:
        # given
        def rename(entity: Record) -> None:
            entity.name = "Robin"

        service = DataS(Record, dependencies=[Depends(rename)])
        # when / then
        async with DataR() as datar:
            created = await service.create(Record(name="Batman"), datar=datar)
            assert created.name == "Robin"
            found = await records.get(created.id, datar=datar)
            assert found is not None
            assert found.name == "Robin"
