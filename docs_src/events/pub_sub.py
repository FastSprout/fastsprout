"""Publish an event and wait for its subscribed handler."""

import asyncio

from fastsprout.events import Event, EventBus, pub, sub

bus = EventBus()


class UserCreated(Event):
    email: str


@sub(UserCreated, bus=bus)
async def send_welcome(event: UserCreated) -> None:
    print(f"Welcome sent to {event.email}")


@pub(bus=bus)
async def register_user() -> UserCreated:
    return UserCreated(email="ada@example.com")


async def main() -> None:
    event = await register_user()
    state = await bus.get(event)
    if state is None:
        raise RuntimeError("The event was not published")
    await state.wait()


if __name__ == "__main__":
    asyncio.run(main())
