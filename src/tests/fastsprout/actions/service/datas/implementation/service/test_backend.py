from uuid import uuid4

import pytest

from fastsprout.actions import DataS
from fastsprout.data import DataR
from fastsprout.data.backend.implementation.signpost import Signpost
from fastsprout.data.capabilities.query import Gte, where
from fastsprout.data.router.exceptions import NoBackendError
from fastsprout.testing.core import given, then, when

from ...common import (
    MemoryAbility,
    MemoryCreate,
    MemoryQuery,
    MemoryRecord,
)
from .common import SelectedMemory, SelectedMemoryActions


class TestSelectedActions:
    @given("selected CRUD actions composed into a Service")
    def service(self) -> SelectedMemoryActions:
        return SelectedMemoryActions()

    @when("the selected create action persists a record")
    async def created(
        self, service: SelectedMemoryActions, memory_context: DataR
    ) -> MemoryRecord:
        return await service.create(
            MemoryCreate("Batman"), datar=memory_context
        )

    @then("the selected get action reads the created record")
    async def test_created(
        self,
        service: SelectedMemoryActions,
        memory_context: DataR,
        created: MemoryRecord,
    ) -> None:
        assert await service.get(created.id, datar=memory_context) == created

    @when("the selected bulk create action persists two more records")
    async def added(
        self,
        service: SelectedMemoryActions,
        memory_context: DataR,
        created: MemoryRecord,
    ) -> list[MemoryRecord]:
        return await service.bulk_create(
            (MemoryCreate(name) for name in ("Robin", "Batgirl")),
            datar=memory_context,
        ).to_list()

    @then("selected bulk actions preserve their input order")
    def test_added(self, added: list[MemoryRecord]) -> None:
        assert [row.name for row in added] == ["Robin", "Batgirl"]

    @when("the selected delete action removes the original record")
    async def deleted(
        self,
        service: SelectedMemoryActions,
        memory_context: DataR,
        created: MemoryRecord,
        added: list[MemoryRecord],
    ) -> int:
        return await service.delete(created.id, datar=memory_context)

    @then("selected CRUD actions share one backend context")
    async def test_deleted(
        self,
        service: SelectedMemoryActions,
        memory_context: DataR,
        memory_backend: MemoryAbility,
        created: MemoryRecord,
        deleted: int,
    ) -> None:
        assert deleted == 1
        assert await service.get(created.id, datar=memory_context) is None
        assert all(
            context is memory_context for context in memory_backend.contexts
        )


@pytest.mark.parametrize("subclass", [False, True])
class TestMemoryCRUD:
    @given("a default or subclassed non-SQL data service")
    def service(self, subclass: bool) -> DataS[MemoryRecord]:
        return SelectedMemory() if subclass else DataS(MemoryRecord)

    @when("a record is created through the default schema")
    async def created(
        self, service: DataS[MemoryRecord], memory_context: DataR
    ) -> MemoryRecord:
        return await service.create(
            service.create_schema(name="Batman"), datar=memory_context
        )

    @then("default schemas and reads preserve the non-SQL entity")
    async def test_created(
        self,
        service: DataS[MemoryRecord],
        memory_context: DataR,
        created: MemoryRecord,
    ) -> None:
        assert service.read_schema is MemoryRecord
        assert service.create_schema is MemoryRecord
        assert isinstance(created, MemoryRecord)
        assert type(created) is MemoryRecord
        assert created.password == "initial"
        assert created.system_key == "system"
        found = await service.get(created.id, datar=memory_context)
        assert found is not None
        assert found.name == "Batman"
        assert await service.exists(created.id, datar=memory_context)
        assert not await service.exists(uuid4(), datar=memory_context)
        assert await service.get(uuid4(), datar=memory_context) is None

    @when("the default update schema replaces the record's name")
    async def updated(
        self,
        service: DataS[MemoryRecord],
        memory_context: DataR,
        created: MemoryRecord,
    ) -> MemoryRecord:
        return await service.update(
            created.id,
            service.update_schema(name="Robin"),
            datar=memory_context,
        )

    @then("non-SQL update returns the updated entity")
    def test_updated(self, updated: MemoryRecord) -> None:
        assert updated.name == "Robin"

    @when("the default patch schema changes the record's score")
    async def patched(
        self,
        service: DataS[MemoryRecord],
        memory_context: DataR,
        updated: MemoryRecord,
    ) -> MemoryRecord:
        return await service.patch(
            updated.id,
            service.patch_schema(name="Robin", score=99),
            datar=memory_context,
        )

    @then("non-SQL patch, list, and count agree on the stored entity")
    async def test_patched(
        self,
        service: DataS[MemoryRecord],
        memory_context: DataR,
        patched: MemoryRecord,
    ) -> None:
        assert (patched.name, patched.score) == ("Robin", 99)
        query = MemoryQuery(MemoryRecord).where(MemoryRecord.score.gte(20))
        page = await service.list(query, datar=memory_context)
        assert (
            page.total == await service.count(query, datar=memory_context) == 1
        )
        assert [(row.id, row.score) for row in page.items] == [(patched.id, 99)]

    @when("the same non-SQL entity is deleted twice")
    async def deleted(
        self,
        service: DataS[MemoryRecord],
        memory_context: DataR,
        patched: MemoryRecord,
    ) -> tuple[int, int]:
        return await service.delete(
            patched.id, datar=memory_context
        ), await service.delete(patched.id, datar=memory_context)

    @then("deletion reports missing records and keeps one shared context")
    async def test_deleted(
        self,
        service: DataS[MemoryRecord],
        memory_context: DataR,
        memory_backend: MemoryAbility,
        deleted: tuple[int, int],
    ) -> None:
        assert deleted == (1, 0)
        assert await service.count(datar=memory_context) == 0
        assert all(
            context is memory_context for context in memory_backend.contexts
        )


@when("a subclassed data service creates matching and non-matching entities")
async def selected_memory(memory_backend: MemoryAbility) -> SelectedMemory:
    service = SelectedMemory()
    await service.create(service.create_schema(name="Batman", score=50))
    await service.create(service.create_schema(name="Robin", score=5))
    return service


@then("non sql service subclass with query")
async def test_non_sql_service_subclass_with_query(
    selected_memory: SelectedMemory,
) -> None:
    query = MemoryQuery(MemoryRecord).where(where(MemoryRecord.score, Gte(20)))
    assert await selected_memory.count(query) == 1
    assert [row.name for row in (await selected_memory.list(query)).items] == [
        "Batman"
    ]


@when("a read uses a signpost without a registered backend")
async def unregistered_read(
    monkeypatch: pytest.MonkeyPatch,
) -> NoBackendError | None:
    monkeypatch.setattr(
        MemoryRecord, "__signpost__", Signpost(lambda: None), raising=False
    )
    service = DataS(MemoryRecord)
    try:
        await service.get(uuid4())
    except NoBackendError as error:
        return error
    return None


@then("unregistered non sql backend fails explicitly")
def test_unregistered_non_sql_backend_fails_explicitly(
    unregistered_read: NoBackendError | None,
) -> None:
    assert isinstance(unregistered_read, NoBackendError)
    assert "Not found backend" in str(unregistered_read)


class DifferentMemoryRecord(MemoryRecord): ...


@when("a query entity and then the selected ability mismatch the service")
async def mismatched_ability(memory_backend: MemoryAbility) -> list[TypeError]:
    service = DataS(MemoryRecord)
    failures: list[TypeError] = []
    try:
        await service.list(MemoryQuery(DifferentMemoryRecord))
    except TypeError as error:
        failures.append(error)
    memory_backend.entity = DifferentMemoryRecord
    try:
        await service.count()
    except TypeError as error:
        failures.append(error)
    return failures


@then("ability must match the service entity")
def test_ability_must_match_the_service_entity(
    mismatched_ability: list[TypeError],
) -> None:
    assert len(mismatched_ability) == 2
    assert "must select the CRUD entity" in str(mismatched_ability[0])
    assert "must use the service entity" in str(mismatched_ability[1])
