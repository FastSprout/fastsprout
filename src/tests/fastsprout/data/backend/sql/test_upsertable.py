import logging

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fastsprout.data.backend.sql import SQLSignpost
from fastsprout.data.backend.sql.capabilities import (
    SQLAbilitable,
    SQLUpsertable,
)
from fastsprout.data.events import CreateEvent, UpdateEvent
from fastsprout.events import EventBus

from .conftest import Hero


class TestSQLUpsertable:
    @pytest.mark.parametrize("capability", [SQLAbilitable, SQLUpsertable])
    async def test_event_lookup_is_limited_to_input_ids(
        self,
        capability: type[SQLUpsertable[Hero]],
        sql_signpost: SQLSignpost,
        sql_session: AsyncSession,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        # given
        await sql_session.commit()
        bus = EventBus()
        ability = capability(sql_signpost, bus=bus)
        inputs = [Hero(id=2, name="updated", age=20), Hero(id=10, name="new")]
        # when
        with caplog.at_level(logging.INFO, logger="sqlalchemy.engine"):
            found = await ability.bulk_upsert(inputs)
        async with ability.bind() as flow:
            await flow.finalize()
        # then
        lookups = [
            record.getMessage()
            for record in caplog.records
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
