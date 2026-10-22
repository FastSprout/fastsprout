import pytest

from fastsprout.data.backend.sql import SQLQuery
from fastsprout.data.events import CreateEvent
from fastsprout.data.router import DataR
from fastsprout.events import EventBus
from fastsprout.testing.core import given, then, when

from .conftest import Item


@pytest.mark.usefixtures("signpost")
class TestTransactions:
    @when("rows are read before a write, before commit and after commit")
    async def reads(self) -> tuple[list[str], list[str], list[str]]:
        async with DataR() as data:
            initial = await data.stream(SQLQuery(Item)).to_list()
            await data.ability(Item).bulk_create(
                [Item(name="a"), Item(name="b")]
            )
            pending = await data.stream(SQLQuery(Item)).to_list()
        async with DataR() as data:
            committed = await data.stream(SQLQuery(Item)).to_list()
        return (
            [row.name for row in initial],
            sorted(row.name for row in pending),
            sorted(row.name for row in committed),
        )

    @then("one context sees its pending writes and clean exit commits them")
    def test_reads_and_writes_in_one_context(
        self, reads: tuple[list[str], list[str], list[str]]
    ) -> None:
        initial, pending, committed = reads
        assert initial == []
        assert pending == ["a", "b"]
        assert committed == pending

    @given("an item without an explicit integer identity")
    def item(self) -> Item:
        return Item(name="generated")

    @when("the item is created and read through a new DataR context")
    async def generated(self, item: Item) -> tuple[bool, Item, Item | None]:
        had_id = "id" in vars(item)
        async with DataR() as data:
            created = await data.ability(Item).create(item)
        async with DataR() as data:
            found = await data.stream(SQLQuery(Item)).first()
        return had_id, created, found

    @then("the database supplies an identity that survives commit")
    def test_database_generates_integer_identity(
        self, item: Item, generated: tuple[bool, Item, Item | None]
    ) -> None:
        had_id, created, found = generated
        assert not had_id
        assert isinstance(created.id, int)
        assert created.id == item.id
        assert found is not None
        assert found.id == created.id

    @when("a write is rolled back by an exception or an explicit abort")
    async def aborted(
        self, bus: EventBus, explicit: bool
    ) -> RuntimeError | None:
        try:
            async with DataR(bus=bus) as data:
                await data.ability(Item).bulk_create([Item(name="x")])
                if explicit:
                    await data.abort()
                else:
                    raise RuntimeError("boom")
        except RuntimeError as error:
            return error
        return None

    @pytest.mark.parametrize(
        "explicit", [False, True], ids=["exception", "abort"]
    )
    @then("rollback discards the write and its buffered creation event")
    async def test_rollback(
        self, bus: EventBus, explicit: bool, aborted: RuntimeError | None
    ) -> None:
        if explicit:
            assert aborted is None
        else:
            assert isinstance(aborted, RuntimeError)
            assert str(aborted) == "boom"
        assert [state async for state in await bus.get(CreateEvent[Item])] == []
        async with DataR() as data:
            assert await data.stream(SQLQuery(Item)).to_list() == []

    @when("the same query is consumed twice in one context")
    async def repeated_reads(self) -> tuple[list[Item], list[Item]]:
        async with DataR() as data:
            first = await data.stream(SQLQuery(Item)).to_list()
            second = await data.stream(SQLQuery(Item)).to_list()
        return first, second

    @then("repeated stream registration reuses the context without errors")
    def test_repeated_stream_shares_session(
        self, repeated_reads: tuple[list[Item], list[Item]]
    ) -> None:
        assert repeated_reads == ([], [])

    @when("a closed router exits a second time")
    async def repeated_exit(self, bus: EventBus) -> list[str]:
        async with DataR(bus=bus) as data:
            await data.ability(Item).create(Item(name="once"))
        await data.__aexit__(None, None, None)
        return [
            state.event.entity.name
            async for state in await bus.get(CreateEvent[Item])
        ]

    @then("repeated exit neither repeats commit nor republishes its events")
    def test_repeated_exit(self, repeated_exit: list[str]) -> None:
        assert repeated_exit == ["once"]
