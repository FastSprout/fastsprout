# Publish and subscribe to events

Install the events extra:

```bash
pip install 'fastsprout[events]'
```

`EventBus` delivers events in memory. In this example, `pub` publishes the
event returned by an action, and `sub` registers a handler for that event type.
Both decorators use the same bus instance.

<!-- example-source: docs_src/events/pub_sub.py -->

```python
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
```

Run the [source file](https://github.com/FastSprout/fastsprout/blob/development/docs_src/events/pub_sub.py)
from the repository root:

```bash
uv run --extra events python docs_src/events/pub_sub.py
```

## Result

```text
Welcome sent to ada@example.com
```

See the [events examples](../learn/examples/index.md) for publishers,
subscriber groups, scheduling, and middleware.
