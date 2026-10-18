import pytest

from fastsprout.actions import DataS, action
from fastsprout.core import Depends, IdentificatorType
from fastsprout.data import DataR

from ...common import Record


class TestDependencyValidation:
    async def test_delete_dependencies_receive_the_key_and_can_reject(
        self,
        records: DataS[Record],
    ) -> None:
        # given
        created = await records.create(Record(name="Batman"))
        calls: list[tuple[IdentificatorType, DataR]] = []

        async def check_exists(
            identifier: IdentificatorType, /, *, datar: DataR
        ) -> None:
            assert await records.exists(identifier, datar=datar)

        @action(dependencies=[Depends(check_exists)])
        async def check_key(
            identifier: IdentificatorType, *, datar: DataR = Depends()
        ) -> None:
            calls.append((identifier, datar))

        @action
        async def reject() -> None:
            raise PermissionError("Cannot delete")

        service = DataS(
            Record, dependencies=[check_key.dependency, Depends(reject)]
        )
        # when
        async with DataR() as datar:
            with pytest.raises(PermissionError, match="Cannot delete"):
                await service.delete(created.id, datar=datar)
        # then
        assert calls == [(created.id, datar)]
        assert await records.exists(created.id)
