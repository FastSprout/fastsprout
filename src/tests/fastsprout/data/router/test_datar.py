import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field as SQLPydField

from fastsprout.core import Depends, Field, inject_depends
from fastsprout.data.backend.sql import SQLEntity
from fastsprout.data.backend.sql.entity import (
    SQL_ENTITY_REGISTRY,
    SQLSignpost,
)
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.events import CreateEvent, DeleteEvent, UpdateEvent
from fastsprout.data.router import DataR
from fastsprout.events import EventBus, sub


class Item(SQLEntity[int]):
    id: Field[int | None] = SQLPydField(  # pyright: ignore[reportIncompatibleVariableOverride, reportAssignmentType]
        default=None, primary_key=True
    )
    name: Field[str] = Field(default="")


@pytest.fixture
async def signpost():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQL_ENTITY_REGISTRY.metadata.create_all)
    bound = SQLSignpost(async_sessionmaker(engine, expire_on_commit=False))
    Item.__signpost__ = bound
    yield bound
    await engine.dispose()


async def test_reads_and_writes_in_one_context(signpost) -> None:
    async with DataR() as data:
        assert await data.stream(SQLQuery(entity=Item)).to_list() == []

        items = data.ability(Item)
        await items.bulk_create([Item(name="a"), Item(name="b")])

        # shared session: reads see uncommitted writes of this context
        rows = await data.stream(SQLQuery(entity=Item)).to_list()
        assert sorted(r.name for r in rows) == ["a", "b"]

    # finalized on clean exit
    async with DataR() as data:
        rows = await data.stream(SQLQuery(entity=Item)).to_list()
        assert sorted(r.name for r in rows) == ["a", "b"]


async def test_exception_aborts_everything(signpost) -> None:
    with pytest.raises(RuntimeError):
        async with DataR() as data:
            items = data.ability(Item)
            await items.bulk_create([Item(name="x")])
            raise RuntimeError("boom")

    async with DataR() as data:
        assert await data.stream(SQLQuery(entity=Item)).to_list() == []


async def test_explicit_abort_mid_context(signpost) -> None:
    async with DataR() as data:
        items = data.ability(Item)
        await items.bulk_create([Item(name="x")])
        await data.abort()

    async with DataR() as data:
        assert await data.stream(SQLQuery(entity=Item)).to_list() == []


async def test_repeated_stream_shares_session(signpost) -> None:
    async with DataR() as data:
        await data.stream(SQLQuery(entity=Item)).to_list()
        await data.stream(SQLQuery(entity=Item)).to_list()
    # one signpost registration, factory wrapped once — no errors


async def test_create_event_uses_concrete_entity_type(signpost) -> None:
    bus = EventBus()
    received: list[Item] = []

    @sub(CreateEvent[Item], bus=bus)
    async def handler(event: CreateEvent[Item]) -> None:
        received.append(event.entity)

    async with DataR(bus=bus) as data:
        await data.ability(Item).create(Item(name="created"))

    states = [state async for state in await bus.get(CreateEvent[Item])]
    assert len(states) == 1
    await states[0].wait()
    assert states[0].result._error_events == []
    assert [item.name for item in received] == ["created"]


async def test_update_event_reaches_subscriber_through_datar(signpost) -> None:
    async with DataR() as data:
        await data.ability(Item).create(Item(name="before"))

    bus = EventBus()
    received: list[Item] = []

    @sub(UpdateEvent[Item], bus=bus)
    async def handler(event: UpdateEvent[Item]) -> None:
        received.append(event.entity)

    async with DataR(bus=bus) as data:
        count = await data.ability(Item).update_by_query(
            SQLQuery(entity=Item), Item.name.set("after")
        )

    states = [state async for state in await bus.get(UpdateEvent[Item])]
    assert len(states) == 1
    await states[0].wait()
    assert states[0].result._error_events == []
    assert count == 1
    assert [item.name for item in received] == ["after"]


async def test_delete_event_reaches_subscriber_through_datar(signpost) -> None:
    async with DataR() as data:
        item = await data.ability(Item).create(Item(name="to delete"))

    bus = EventBus()
    received: list[int] = []

    @sub(DeleteEvent[int], bus=bus)
    async def handler(event: DeleteEvent[int]) -> None:
        received.append(event.id)

    async with DataR(bus=bus) as data:
        count = await data.ability(Item).delete(item)

    states = [state async for state in await bus.get(DeleteEvent[int])]
    assert len(states) == 1
    await states[0].wait()
    assert states[0].result._error_events == []
    assert count == 1
    assert received == [item.id]


async def test_dependencies_receive_operation_entity_and_same_router(signpost):
    calls: list[tuple[str, str]] = []
    dependency = Depends()

    def check(
        operation: str, entity: Item | None = None, datar: DataR = dependency
    ) -> None:
        assert datar is data
        calls.append((operation, "" if entity is None else entity.name))

    async with DataR(dependencies=[Depends(check)]) as data:
        items = data.ability(Item)
        created = await items.create(Item(name="Batman"))
        assert calls == [("create", "Batman")]
        await items.find_first(SQLQuery(entity=Item))
        await items.delete(created)
    assert calls == [
        ("create", "Batman"),
        ("find_first", ""),
        ("delete", "Batman"),
    ]


async def test_rejected_dependency_prevents_write_and_stops_chain(signpost):
    def reject(operation: str) -> None:
        assert operation == "create"
        raise PermissionError("Forbidden")

    def never() -> None:
        raise AssertionError("Dependency chain continued")

    with pytest.raises(PermissionError, match="Forbidden"):
        async with DataR(
            dependencies=[Depends(reject), Depends(never)]
        ) as data:
            await data.ability(Item).create(Item(name="Batman"))
    async with DataR() as data:
        assert await data.stream(SQLQuery(entity=Item)).count() == 0


@pytest.mark.parametrize("read", ["count", "first", "values", "iterate"])
async def test_read_dependencies_are_lazy_and_guard_derived_sql_streams(
    signpost, read: str
):
    calls: list[str] = []

    def reject(operation: str, query: SQLQuery[Item], datar: DataR) -> None:
        assert datar is data
        assert query.entity is Item
        calls.append(operation)
        raise PermissionError("Cannot read")

    async with DataR(dependencies=[Depends(reject)]) as data:
        stream = data.ability(Item).stream(SQLQuery(entity=Item)).take(1)
        assert calls == []
        with pytest.raises(PermissionError, match="Cannot read"):
            if read == "count":
                await stream.count()
            elif read == "first":
                await stream.first()
            elif read == "values":
                await stream.to_values(Item.name).to_list()
            else:
                await stream.to_list()
    assert calls == ["read"]


async def test_bulk_create_checks_once(signpost):
    calls: list[str] = []

    def check(operation: str) -> None:
        calls.append(operation)

    async with DataR(dependencies=[Depends(check)]) as data:
        created = await data.ability(Item).bulk_create(
            [Item(name="Batman"), Item(name="Robin")]
        )
        assert [item.name for item in created] == ["Batman", "Robin"]
    assert calls == ["bulk_create"]


async def test_iteration_dependencies_precede_consuming_generator(signpost):
    consumed: list[str] = []

    async def entities() -> AsyncIterator[Item]:
        consumed.append("entity")
        yield Item(name="Batman")

    def reject(operation: str) -> None:
        assert operation == "iter_bulk_create"
        raise PermissionError("Cannot create")

    async with DataR(dependencies=[Depends(reject)]) as data:
        stream = data.ability(Item).iter_bulk_create(entities())
        assert consumed == []
        with pytest.raises(PermissionError, match="Cannot create"):
            await anext(stream)
    assert consumed == []


async def test_class_router_dependencies_can_be_overridden(signpost):
    def reject() -> None:
        raise PermissionError("Forbidden")

    class GuardedDataR(DataR):
        dependencies = (Depends(reject),)

    with pytest.raises(PermissionError, match="Forbidden"):
        async with GuardedDataR() as data:
            await data.ability(Item).create(Item(name="Batman"))
    async with GuardedDataR(dependencies=[]) as data:
        assert (
            await data.ability(Item).create(Item(name="Robin"))
        ).name == "Robin"


async def test_nested_dependency_cache_rechecks_each_operation(signpost):
    calls: list[str] = []

    def allowed_operation(operation: str) -> bool:
        calls.append(operation)
        return operation != "delete"

    def check_access(allowed: bool = Depends(allowed_operation)) -> None:
        if not allowed:
            raise PermissionError("Cannot delete")

    @inject_depends
    async def run() -> None:
        async with DataR(dependencies=[Depends(check_access)]) as data:
            ability = data.ability(Item)
            entity = await ability.create(Item(name="Batman"))
            with pytest.raises(PermissionError, match="Cannot delete"):
                await ability.delete(entity)
            assert await ability.find_first(SQLQuery(entity=Item)) == entity

    await run()
    assert calls == ["create", "delete", "find_first"]


@pytest.mark.parametrize("same_ability", [False, True])
async def test_dependency_can_query_same_router(signpost, same_ability: bool):
    calls: list[str] = []

    async def validate(
        operation: str,
        datar: Annotated[DataR, Depends()],
        entity: Item | None = None,
    ) -> None:
        calls.append(operation)
        if entity is not None:
            reader = ability if same_ability else datar.ability(Item)
            assert await reader.find_first(SQLQuery(entity=Item)) is None

    async with asyncio.timeout(2):
        async with DataR(dependencies=[Depends(validate)]) as data:
            ability = data.ability(Item)
            created = await ability.create(Item(name="Batman"))
            assert created.name == "Batman"
    assert calls == ["create", "find_first"]


async def test_child_task_cannot_inherit_dependency_bypass(signpost):
    calls: list[str] = []
    ready: asyncio.Future[Item] = asyncio.get_running_loop().create_future()
    pending: asyncio.Task[int] | None = None

    async def delete_later() -> int:
        return await ability.delete(await ready)

    def check_access(operation: str) -> None:
        nonlocal pending
        calls.append(operation)
        if operation == "create":
            pending = asyncio.create_task(delete_later())
        if operation == "delete":
            raise PermissionError("Cannot delete")

    async with DataR(dependencies=[Depends(check_access)]) as data:
        ability = data.ability(Item)
        ready.set_result(await ability.create(Item(name="Batman")))
        assert pending is not None
        with pytest.raises(PermissionError, match="Cannot delete"):
            await pending
        assert await ability.find_first(SQLQuery(entity=Item)) is not None
    assert calls == ["create", "delete", "find_first"]
