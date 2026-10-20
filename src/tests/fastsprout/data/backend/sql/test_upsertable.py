import logging
from collections.abc import Sequence

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.data.backend.sql import SQLSignpost
from fastsprout.data.backend.sql.capabilities import (
    SQLAbilitable,
    SQLUpsertable,
)
from fastsprout.data.events import CreateEvent, UpdateEvent
from fastsprout.events import EventBus
from fastsprout.testing.core import given, then, when

from .conftest import Hero


class TestSQLUpsertable:
    @given("committed heroes and an upsert ability publishing data events")
    async def ability(
        self,
        capability: type[SQLUpsertable[Hero]],
        sql_signpost: SQLSignpost,
        sql_session: AsyncSession,
        bus: EventBus,
    ) -> SQLUpsertable[Hero]:
        await sql_session.commit()
        return capability(sql_signpost, bus=bus)

    @when("one existing and one new hero are upserted and events finalized")
    async def found(
        self,
        ability: SQLUpsertable[Hero],
        caplog: pytest.LogCaptureFixture,
    ) -> Sequence[Hero]:
        inputs = [Hero(id=2, name="updated", age=20), Hero(id=10, name="new")]
        with caplog.at_level(logging.INFO, logger="sqlalchemy.engine"):
            found = await ability.bulk_upsert(inputs)
        async with ability.bind() as flow:
            await flow.finalize()
        return found

    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLUpsertable])
    @then("upsert looks up only input IDs and emits the matching event kinds")
    async def test_event_lookup_is_limited_to_input_ids(
        self,
        found: Sequence[Hero],
        bus: EventBus,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        lookups = [
            record.getMessage()
            for record in caplog.get_records("setup")
            if record.getMessage().startswith("SELECT hero.id")
        ]
        assert len(lookups) == 1
        assert "WHERE hero.id IN" in lookups[0]
        assert {(hero.id, hero.name) for hero in found} == {
            (2, "updated"),
            (10, "new"),
        }
        created = [
            state.event.entity.id
            async for state in await bus.get(CreateEvent[Hero])
        ]
        updated = [
            state.event.entity.id
            async for state in await bus.get(UpdateEvent[Hero])
        ]
        assert created == [10]
        assert updated == [2]
