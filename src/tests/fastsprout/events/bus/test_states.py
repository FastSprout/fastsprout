from fastsprout.events import EventBus, EventState
from fastsprout.events.event import Eventable
from fastsprout.testing.core import given, then, when

from ..backend.base_test_broker import Message


class TestEventStates:
    @given("two distinct messages with identical content")
    def messages(self) -> tuple[Message, Message]:
        return Message(value=1), Message(value=1)

    @when("both messages are published")
    async def published(
        self, bus: EventBus, messages: tuple[Message, Message]
    ) -> tuple[EventState[Message], EventState[Message]]:
        first, second = messages
        return await bus.publish(first), await bus.publish(second)

    @then("identical messages have separate identities and stored states")
    async def test_event_ids_separate_events_of_the_same_type(
        self,
        bus: EventBus,
        messages: tuple[Message, Message],
        published: tuple[EventState[Message], EventState[Message]],
    ) -> None:
        first, second = messages
        assert first.__event_id__ != second.__event_id__
        assert first.__event_id__ == first.__event_id__
        assert "_event_id" not in first.model_dump()
        assert await bus.get(first) is published[0]
        assert await bus.get(second) is published[1]

    @when("the first published message is retracted")
    async def retracted(
        self,
        bus: EventBus,
        published: tuple[EventState[Message], EventState[Message]],
    ) -> bool:
        return await bus.retract(published[0])

    @then("retraction removes only the selected event state")
    async def test_retraction_preserves_other_event(
        self,
        bus: EventBus,
        published: tuple[EventState[Message], EventState[Message]],
        retracted: bool,
    ) -> None:
        assert retracted
        assert await bus.get(published[0].event) is None
        assert await bus.get(published[1].event) is published[1]

    @given("a subscriber returning the next message")
    def responding_bus(self, bus: EventBus) -> EventBus:
        async def next_message(event: Message) -> Message:
            return Message(value=event.value + 1)

        bus.subscribe(Message, next_message)
        return bus

    @when("two messages are published and the first result is awaited")
    async def representations(
        self, responding_bus: EventBus
    ) -> tuple[str, str, str]:
        first = Message(value=1)
        second = Message(value=2)
        first_state = await responding_bus.publish(first)
        second_state = await responding_bus.publish(second)
        group = await responding_bus.get(first, second)
        result = await first_state.wait()
        await second_state.wait()
        return repr(first_state), repr(group), repr(result)

    @then("state, group and result representations expose event values")
    def test_event_wrapper_reprs_show_events_and_results(
        self, representations: tuple[str, str, str]
    ) -> None:
        state, group, result = representations
        assert state == "EventState(event=Message(value=1))"
        assert group == (
            "EventStatesGroup(EventState(event=Message(value=1)), "
            "EventState(event=Message(value=2)))"
        )
        assert result == (
            "EventResult(state=EventState(event=Message(value=1)), "
            "values=[Message(value=2)], pending=0, errors=[])"
        )

    @when("two messages are published through the EventBus context manager")
    async def group_delivery(
        self, responding_bus: EventBus, messages: tuple[Message, Message]
    ) -> tuple[EventState[Message] | None, list[EventState[Eventable]]]:
        async with responding_bus(*messages) as group:
            first = await group.get(messages[0])
            completed = [state async for state in group.as_completed()]
        return first, completed

    @then("event groups expose their stored states and every completed event")
    def test_group_delivery(
        self,
        group_delivery: tuple[
            EventState[Message] | None, list[EventState[Eventable]]
        ],
        messages: tuple[Message, Message],
    ) -> None:
        first, completed = group_delivery
        assert first is not None
        assert first.event is messages[0]
        assert {state.event.__event_id__ for state in completed} == {
            event.__event_id__ for event in messages
        }
        assert all(not state.result.errors for state in completed)

    @when("completion is requested before entering an event group")
    async def unopened_group(self, bus: EventBus) -> RuntimeError | None:
        group = bus(Message(value=1))
        try:
            await anext(group.as_completed())
        except RuntimeError as error:
            return error
        return None

    @then("an unopened event group rejects iteration")
    def test_unopened_group(self, unopened_group: RuntimeError | None) -> None:
        assert isinstance(unopened_group, RuntimeError)
        assert "not entered" in str(unopened_group)

    @when("publish is called without events")
    async def empty_publication(self, bus: EventBus) -> RuntimeError | None:
        try:
            await bus.publish()
        except RuntimeError as error:
            return error
        return None

    @then("empty publication is rejected")
    def test_empty_publication(
        self, empty_publication: RuntimeError | None
    ) -> None:
        assert isinstance(empty_publication, RuntimeError)
        assert "Not provided" in str(empty_publication)

    @when("the same event identity is published a second time")
    async def duplicate(
        self,
        bus: EventBus,
        published: tuple[EventState[Message], EventState[Message]],
    ) -> ValueError | None:
        try:
            await bus.publish(published[0].event)
        except ValueError as error:
            return error
        return None

    @then("duplicate event identities are rejected")
    def test_duplicate(self, duplicate: ValueError | None) -> None:
        assert isinstance(duplicate, ValueError)
        assert "already dispatched" in str(duplicate)

    @when("a group containing unpublished messages is requested")
    async def missing_group(
        self, bus: EventBus, messages: tuple[Message, Message]
    ) -> LookupError | None:
        try:
            await bus.get(*messages)
        except LookupError as error:
            return error
        return None

    @then("missing group members are reported instead of silently omitted")
    def test_missing_group(self, missing_group: LookupError | None) -> None:
        assert isinstance(missing_group, LookupError)
        assert "not published" in str(missing_group)
