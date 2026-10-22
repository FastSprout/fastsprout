import pytest

from fastsprout.actions import DataS
from fastsprout.data import DataR
from fastsprout.data.capabilities.query import Eq, where
from fastsprout.data.utils.iterable import resolve_any_iterable
from fastsprout.testing.core import given, then, when

from ...common import (
    MemoryAbility,
    MemoryCreate,
    MemoryPatch,
    MemoryQuery,
    MemoryRecord,
)

type MemoryDataS = DataS[
    MemoryRecord, MemoryRecord, MemoryCreate, MemoryRecord, MemoryPatch
]


class BaseMemoryBulk:
    names = ("Batman", "Robin", "Batgirl")

    @given("a non-SQL service with dataclass create and patch schemas")
    def service(
        self,
    ) -> MemoryDataS:
        return DataS(
            MemoryRecord, create=MemoryCreate, patch=MemoryPatch, chunk_size=2
        )

    @when("dataclass payloads are bulk-created from the requested iterable")
    async def created(
        self,
        service: MemoryDataS,
        memory_context: DataR,
        asynchronous: bool,
    ) -> list[MemoryRecord]:
        payloads = (MemoryCreate(name) for name in self.names)
        return await service.bulk_create(
            resolve_any_iterable(payloads) if asynchronous else payloads,
            datar=memory_context,
        ).to_list()

    @when("every created record is bulk-patched")
    async def patched(
        self,
        service: MemoryDataS,
        memory_context: DataR,
        created: list[MemoryRecord],
        asynchronous: bool,
    ) -> list[MemoryRecord]:
        patches = ((row.id, MemoryPatch(score=20)) for row in created)
        return await service.bulk_patch(
            resolve_any_iterable(patches) if asynchronous else patches,
            datar=memory_context,
        ).to_list()

    @when("the patched records are bulk-deleted")
    async def deleted(
        self,
        service: MemoryDataS,
        memory_context: DataR,
        patched: list[MemoryRecord],
        asynchronous: bool,
    ) -> int:
        identifiers = (row.id for row in patched)
        return await service.bulk_delete(
            resolve_any_iterable(identifiers) if asynchronous else identifiers,
            datar=memory_context,
        )


@pytest.mark.parametrize("asynchronous", [False, True])
class TestBulkSchemas(BaseMemoryBulk):
    @then("bulk create preserves the dataclass input order")
    def test_created(self, created: list[MemoryRecord]) -> None:
        assert [row.name for row in created] == list(self.names)

    @then("bulk patch preserves IDs and applies every payload")
    def test_patched(
        self, created: list[MemoryRecord], patched: list[MemoryRecord]
    ) -> None:
        assert [row.id for row in patched] == [row.id for row in created]
        assert [row.score for row in patched] == [20, 20, 20]

    @then("bulk delete empties the shared non-SQL context")
    def test_deleted(
        self, deleted: int, memory_backend: MemoryAbility, memory_context: DataR
    ) -> None:
        assert deleted == 3
        assert memory_backend.items == {}
        assert all(
            context is memory_context for context in memory_backend.contexts
        )


@pytest.mark.parametrize("asynchronous", [False])
class TestMemoryQueryAndBulk(BaseMemoryBulk):
    names = ("Batman", "Batgirl", "Robin")

    @when("bulk streams are constructed with non-positive chunk sizes")
    def invalid_chunk_sizes(self) -> list[ValueError]:
        failures: list[ValueError] = []
        for size in (0, -1):
            invalid = DataS(MemoryRecord, chunk_size=size)
            try:
                invalid.bulk_create([])
            except ValueError as error:
                failures.append(error)
        return failures

    @then(
        "non-SQL queries apply filters, pagination, native statements, and field guards"
    )
    async def test_query(
        self,
        service: MemoryDataS,
        memory_context: DataR,
        created: list[MemoryRecord],
        invalid_chunk_sizes: list[ValueError],
    ) -> None:
        assert len(invalid_chunk_sizes) == 2
        assert all(
            "chunk_size must be positive" in str(error)
            for error in invalid_chunk_sizes
        )
        query = (
            MemoryQuery(MemoryRecord)
            .where(where(MemoryRecord.name, "BAT"))
            .limit(1)
        )
        page = await service.list(query, datar=memory_context)
        assert page.total == 2
        assert [row.name for row in page.items] == ["Batman"]
        assert await service.count(query, datar=memory_context) == 2
        selection = MemoryQuery(MemoryRecord, statement="Robin")
        assert await service.count(selection, datar=memory_context) == 1
        assert [
            row.name
            for row in (
                await service.list(selection, datar=memory_context)
            ).items
        ] == ["Robin"]
        with pytest.raises(AttributeError, match="public field"):
            await service.count(
                MemoryQuery(MemoryRecord).where(
                    where(MemoryRecord.system_key, Eq("system"))
                ),
                datar=memory_context,
            )

    @then("non-SQL dataclass patches apply to every record")
    def test_patched(self, patched: list[MemoryRecord]) -> None:
        assert [row.score for row in patched] == [20, 20, 20]

    @when("patched entities are passed to bulk update")
    async def updated(
        self,
        service: MemoryDataS,
        memory_context: DataR,
        patched: list[MemoryRecord],
    ) -> list[MemoryRecord]:
        return await service.bulk_update(
            iter(patched), datar=memory_context
        ).to_list()

    @then("non-SQL bulk update preserves the entity order")
    def test_updated(self, updated: list[MemoryRecord]) -> None:
        assert [row.name for row in updated] == list(self.names)

    @when("the updated entities are bulk-deleted")
    async def deleted_updated(
        self,
        service: MemoryDataS,
        memory_context: DataR,
        updated: list[MemoryRecord],
    ) -> int:
        return await service.bulk_delete(
            (row.id for row in updated), datar=memory_context
        )

    @then("bulk-deleted updated entities disappear from the backend")
    async def test_deleted(
        self,
        service: MemoryDataS,
        memory_context: DataR,
        deleted_updated: int,
    ) -> None:
        assert deleted_updated == 3
        assert await service.count(datar=memory_context) == 0
