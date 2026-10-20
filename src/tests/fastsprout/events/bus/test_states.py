from fastsprout.events import EventBus, EventState
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
