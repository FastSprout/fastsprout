from uuid import uuid4

import pytest

from fastsprout.actions import DataS
from fastsprout.data import DataR

from ...common import (
    MemoryAbility,
    MemoryRecord,
)


@pytest.fixture
def memory_backend(monkeypatch: pytest.MonkeyPatch) -> MemoryAbility:
    backend = MemoryAbility()

    def ability(datar: DataR, entity: type[MemoryRecord]) -> MemoryAbility:
        if entity is not backend.entity:
            raise TypeError("Ability must use the service entity")
        backend.contexts.append(datar)
        return backend

    monkeypatch.setattr(DataR, "ability", ability)
    return backend


class TestBackend:
    async def test_non_sql_crud_uses_entity_and_one_context(
        self,
        memory_backend: MemoryAbility,
    ) -> None:
        # given
        service = DataS(MemoryRecord)
        assert service.read_schema is MemoryRecord
        assert service.create_schema is MemoryRecord
        # when / then
        async with DataR() as datar:
            created = await service.create(
                service.create_schema(name="Batman"), datar=datar
            )
            assert isinstance(created, MemoryRecord)
            assert type(created) is MemoryRecord
            assert created.password == "initial"
            assert created.system_key == "system"
            found = await service.get(created.id, datar=datar)
            assert found is not None
            assert found.name == "Batman"
            assert await service.exists(created.id, datar=datar)
            assert not await service.exists(uuid4(), datar=datar)
            assert await service.get(uuid4(), datar=datar) is None
            updated = await service.update(
                created.id, service.update_schema(name="Robin"), datar=datar
            )
            assert updated.name == "Robin"
            patched = await service.patch(
                created.id,
                service.patch_schema(name="Robin", score=99),
                datar=datar,
            )
            assert (patched.name, patched.score) == ("Robin", 99)
            assert await service.delete(created.id, datar=datar) == 1
            assert await service.delete(created.id, datar=datar) == 0
            assert all(context is datar for context in memory_backend.contexts)
