from collections.abc import AsyncIterator, Sequence

import pytest

from fastsprout.core import Depends
from fastsprout.data.backend.sql import SQLQuery, SQLSignpost
from fastsprout.data.router import DataR
from fastsprout.data.router.implementation.dependencies import (
    AbilityDependencies,
)
from fastsprout.testing.core import given, then, when

from .conftest import Item

type DependencyCall = tuple[str, str, DataR]


@pytest.mark.usefixtures("signpost")
class TestDependencies:
    @when("a dependency guard is attached to an unbound backend signpost")
    def unbound_stream(self, signpost: SQLSignpost) -> TypeError | None:
        async def read() -> None:
            raise AssertionError("An unbound stream must not execute")

        guard = AbilityDependencies(DataR(), ())
        try:
            guard.stream(signpost, read)
        except TypeError as error:
            return error
        return None

    @then("stream dependencies require the router's transaction binding")
    def test_unbound_stream(self, unbound_stream: TypeError | None) -> None:
        assert isinstance(unbound_stream, TypeError)
        assert str(unbound_stream) == (
            "A router stream requires its bound signpost"
        )

    @given("a recorder of dependency operation names")
    def calls(self) -> list[str]:
        return []

    @given("a recorder of operation, entity and router arguments")
    def entity_calls(self) -> list[DependencyCall]:
        return []

    @when("create, find and delete run through one router")
    async def executed(
        self, entity_calls: list[DependencyCall]
    ) -> tuple[list[DependencyCall], DataR]:
        dependency = Depends()

        def check(
            operation: str,
            entity: Item | None = None,
            datar: DataR = dependency,
        ) -> None:
            entity_calls.append(
                (operation, "" if entity is None else entity.name, datar)
            )

        async with DataR(dependencies=[Depends(check)]) as data:
            items = data.ability(Item)
            created = await items.create(Item(name="Batman"))
            after_create = entity_calls.copy()
            await items.find_first(SQLQuery(Item))
            await items.delete(created)
        return after_create, data

    @then("each dependency receives its operation, entity and shared router")
    def test_operation_arguments(
        self,
        executed: tuple[list[DependencyCall], DataR],
        entity_calls: list[DependencyCall],
    ) -> None:
        after_create, data = executed
        assert [(operation, name) for operation, name, _ in after_create] == [
            ("create", "Batman")
        ]
        assert [(operation, name) for operation, name, _ in entity_calls] == [
            ("create", "Batman"),
            ("find_first", ""),
            ("delete", "Batman"),
        ]
        assert all(router is data for _, _, router in entity_calls)

    @when("the first dependency rejects a write")
    async def rejected_write(self, calls: list[str]) -> PermissionError | None:
        def reject(operation: str) -> None:
            calls.append(operation)
            raise PermissionError("Forbidden")

        def never() -> None:
            calls.append("unexpected")
            raise AssertionError("Dependency chain continued")

        try:
            async with DataR(
                dependencies=[Depends(reject), Depends(never)]
            ) as data:
                await data.ability(Item).create(Item(name="Batman"))
        except PermissionError as error:
            return error
        return None

    @then("rejection stops the dependency chain and prevents persistence")
    async def test_rejected_write(
        self, rejected_write: PermissionError | None, calls: list[str]
    ) -> None:
        assert isinstance(rejected_write, PermissionError)
        assert str(rejected_write) == "Forbidden"
        assert calls == ["create"]
        async with DataR() as data:
            assert await data.stream(SQLQuery(Item)).count() == 0

    @given("a recorder of consumed input items")
    def consumed(self) -> list[str]:
        return []

    @given("an asynchronous source of two new items")
    def source(self, consumed: list[str]) -> AsyncIterator[Item]:
        async def entities() -> AsyncIterator[Item]:
            for name in ("Batman", "Robin"):
                consumed.append(name)
                yield Item(name=name)

        return entities()

    @when("bulk create consumes an asynchronous source")
    async def created(
        self, calls: list[str], source: AsyncIterator[Item]
    ) -> Sequence[Item]:
        def check(operation: str) -> None:
            calls.append(operation)

        async with DataR(dependencies=[Depends(check)]) as data:
            return await data.ability(Item).bulk_create(source)

    @then("bulk create accepts all async items and checks dependencies once")
    def test_bulk_create(
        self, created: Sequence[Item], calls: list[str], consumed: list[str]
    ) -> None:
        assert [item.name for item in created] == ["Batman", "Robin"]
        assert consumed == ["Batman", "Robin"]
        assert calls == ["bulk_create"]

    @when("a rejecting dependency guards a lazy bulk-create iterator")
    async def rejected_iteration(
        self, source: AsyncIterator[Item], calls: list[str], consumed: list[str]
    ) -> tuple[tuple[str, ...], PermissionError | None]:
        def reject(operation: str) -> None:
            calls.append(operation)
            raise PermissionError("Cannot create")

        async with DataR(dependencies=[Depends(reject)]) as data:
            stream = data.ability(Item).iter_bulk_create(source)
            before = tuple(consumed)
            try:
                await anext(stream)
            except PermissionError as error:
                return before, error
        return before, None

    @then("iteration checks dependencies before consuming any input")
    def test_iteration_rejection(
        self,
        rejected_iteration: tuple[tuple[str, ...], PermissionError | None],
        calls: list[str],
        consumed: list[str],
    ) -> None:
        before, error = rejected_iteration
        assert before == ()
        assert isinstance(error, PermissionError)
        assert str(error) == "Cannot create"
        assert calls == ["iter_bulk_create"]
        assert consumed == []
