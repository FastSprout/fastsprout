from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from fastsprout.data import DataR
from fastsprout.data.backend.sql.entity import SQL_ENTITY_REGISTRY
from fastsprout.data.streams.protocols import AsyncEntityStreamable
from fastsprout.testing.core import given

from ...common import (
    MemoryAbility,
    MemoryQuery,
    MemoryRecord,
)
from .common import engine


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
    ) -> AsyncEntityStreamable[MemoryRecord]:
        return ability(datar, query.entity).stream(query)

    monkeypatch.setattr(DataR, "ability", ability)
    monkeypatch.setattr(DataR, "stream", stream)
    return backend


@given("a shared DataR context for the memory backend")
async def memory_context(memory_backend: MemoryAbility) -> AsyncIterator[DataR]:
    async with DataR() as datar:
        yield datar


@given("prepared SQL entity tables with cleanup after the scenario")
async def prepared_tables() -> AsyncIterator[AsyncEngine]:
    async with engine.begin() as connection:
        await connection.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()
