from typing import Literal

import pytest

from fastsprout.core import dataclass
from fastsprout.data.backend.sql import SQLQuery, SQLSignpost
from fastsprout.data.events import CreateEvent, DeleteEvent, UpdateEvent
from fastsprout.data.router import DataR
from fastsprout.events import EventBus
from fastsprout.testing.core import given, then, when

from .conftest import Item

type Operation = Literal["create", "update", "delete"]
type ItemEvent = CreateEvent[Item] | UpdateEvent[Item] | DeleteEvent[int]


@dataclass
class Delivery:
    before_commit: int
    after_commit: int
    errors: tuple[BaseException, ...]
    affected: int | None
    identity: int


@pytest.mark.parametrize("operation", ["create", "update", "delete"])
class TestDataEvents:
    @given("a recorder of delivered entities and deleted identities")
    def received(self) -> list[Item | int]:
        return []

    @given("subscribers for concrete create, update and delete event types")
    def subscribed_bus(
        self, bus: EventBus, received: list[Item | int]
    ) -> EventBus:
        async def entity_handler(
            event: CreateEvent[Item] | UpdateEvent[Item],
        ) -> None:
            received.append(event.entity)

        async def delete_handler(event: DeleteEvent[int]) -> None:
            received.append(event.id)

        bus.subscribe(CreateEvent[Item], entity_handler)
        bus.subscribe(UpdateEvent[Item], entity_handler)
        bus.subscribe(DeleteEvent[int], delete_handler)
        return bus

    @given("a new item for create or a persisted item for update and delete")
    async def item(self, operation: Operation, signpost: SQLSignpost) -> Item:
        item = Item(name="created" if operation == "create" else "before")
        if operation != "create":
            async with signpost.factory() as session:
                session.add(item)
                await session.commit()
        return item

    @when("the operation commits and its event handlers finish")
    async def delivered(
        self, operation: Operation, item: Item, subscribed_bus: EventBus
    ) -> Delivery:
        event_type: type[ItemEvent] = (
            CreateEvent[Item]
            if operation == "create"
            else UpdateEvent[Item]
            if operation == "update"
            else DeleteEvent[int]
        )
        affected: int | None = None
        async with DataR(bus=subscribed_bus) as data:
            ability = data.ability(Item)
            if operation == "create":
                await ability.create(item)
            elif operation == "update":
                affected = await ability.update_by_query(
                    SQLQuery(Item), Item.name.set("after")
                )
            else:
                affected = await ability.delete(item)
            before_commit = len(
                [state async for state in await subscribed_bus.get(event_type)]
            )
            if operation == "create":
                await data.finalize()
        states = [state async for state in await subscribed_bus.get(event_type)]
        for state in states:
            await state.wait()
        return Delivery(
            before_commit,
            len(states),
            tuple(error for state in states for error in state.result.errors),
            affected,
            item.id,
        )

    @then(
        "events are buffered until commit and delivered with their concrete type"
    )
    def test_delivery(
        self,
        operation: Operation,
        delivered: Delivery,
        received: list[Item | int],
    ) -> None:
        assert delivered.before_commit == 0
        assert delivered.after_commit == 1
        assert delivered.errors == ()
        if operation != "create":
            assert delivered.affected == 1
        if operation == "delete":
            assert received == [delivered.identity]
        else:
            assert len(received) == 1
            assert isinstance(received[0], Item)
            assert received[0].name == (
                "created" if operation == "create" else "after"
            )
