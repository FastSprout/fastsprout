from uuid import uuid4

import pytest

from fastsprout.actions import DataS, Service
from fastsprout.actions.service.datas.implementation import commands, queries
from fastsprout.data import DataR
from fastsprout.data.streams.protocols import AsyncEntityStream
from fastsprout.data.utils.iterable import resolve_any_iterable
from fastsprout.testing.core import given, when_then

from ...common import (
    MemoryAbility,
    MemoryCreate,
    MemoryPatch,
    MemoryQuery,
    MemoryRecord,
)


@given("an in-memory backend shared by ability and stream routing")
def memory_backend(monkeypatch: pytest.MonkeyPatch) -> MemoryAbility:
    backend = MemoryAbility()

    def ability(datar: DataR, entity: type[MemoryRecord]) -> MemoryAbility:
        if entity is not backend.entity:
            raise TypeError("Ability must use the service entity")
        backend.contexts.append(datar)
        return backend

    def stream(
        datar: DataR, query: MemoryQuery
    ) -> AsyncEntityStream[MemoryRecord]:
        return ability(datar, query.entity).stream(query)

    monkeypatch.setattr(DataR, "ability", ability)
    monkeypatch.setattr(DataR, "stream", stream)
    return backend


class SelectedMemoryActions(Service):
    entity = MemoryRecord
    read_schema = MemoryRecord
    create_schema = MemoryCreate
    chunk_size = 2

    create = commands.create
    bulk_create = commands.bulk_create
    get = queries.get
    delete = commands.delete


class TestBackend:
    @when_then("selected CRUD actions compose into an ordinary Service")
    async def test_selected_actions_share_backend_context(
        self, memory_backend: MemoryAbility
    ) -> None:
        service = SelectedMemoryActions()
        async with DataR() as datar:
            created = await service.create(MemoryCreate("Batman"), datar=datar)
            assert await service.get(created.id, datar=datar) == created
            added = await service.bulk_create(
                (MemoryCreate(name) for name in ("Robin", "Batgirl")),
                datar=datar,
            ).to_list()
            assert [row.name for row in added] == ["Robin", "Batgirl"]
            assert await service.delete(created.id, datar=datar) == 1
            assert await service.get(created.id, datar=datar) is None
            assert all(context is datar for context in memory_backend.contexts)

    @when_then("CRUD and paginated reads use the same non-SQL backend context")
    async def test_non_sql_crud_uses_entity_and_one_context(
        self,
        memory_backend: MemoryAbility,
    ) -> None:
        service = DataS(MemoryRecord)
        assert service.read_schema is MemoryRecord
        assert service.create_schema is MemoryRecord
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
            query = MemoryQuery(MemoryRecord).where(MemoryRecord.score.gte(20))
            page = await service.list(query, datar=datar)
            assert page.total == await service.count(query, datar=datar) == 1
            assert [(row.id, row.score) for row in page.items] == [
                (created.id, 99)
            ]
            assert await service.delete(created.id, datar=datar) == 1
            assert await service.delete(created.id, datar=datar) == 0
            assert await service.count(datar=datar) == 0
            assert all(context is datar for context in memory_backend.contexts)

    @when_then("non-SQL bulk actions accept sync and async schema inputs")
    @pytest.mark.parametrize("asynchronous", [False, True])
    async def test_bulk_schema_inputs(
        self, memory_backend: MemoryAbility, asynchronous: bool
    ) -> None:
        service = DataS(
            MemoryRecord, create=MemoryCreate, patch=MemoryPatch, chunk_size=2
        )
        async with DataR() as datar:
            payloads = (
                MemoryCreate(name) for name in ("Batman", "Robin", "Batgirl")
            )
            created = await service.bulk_create(
                resolve_any_iterable(payloads) if asynchronous else payloads,
                datar=datar,
            ).to_list()
            assert [row.name for row in created] == [
                "Batman",
                "Robin",
                "Batgirl",
            ]
            patches = ((row.id, MemoryPatch(score=20)) for row in created)
            patched = await service.bulk_patch(
                resolve_any_iterable(patches) if asynchronous else patches,
                datar=datar,
            ).to_list()
            assert [row.id for row in patched] == [row.id for row in created]
            assert [row.score for row in patched] == [20, 20, 20]
            identifiers = (row.id for row in patched)
            assert (
                await service.bulk_delete(
                    resolve_any_iterable(identifiers)
                    if asynchronous
                    else identifiers,
                    datar=datar,
                )
                == 3
            )
            assert memory_backend.items == {}
            assert all(context is datar for context in memory_backend.contexts)
