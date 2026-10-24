import asyncio
from typing import Annotated

import pytest

from fastsprout.core import Depends, inject_depends
from fastsprout.data.backend.sql.query import SQLQuery
from fastsprout.data.router import DataR

from .conftest import Item


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
