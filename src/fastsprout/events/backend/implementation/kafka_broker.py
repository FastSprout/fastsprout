from collections.abc import Awaitable, Callable

from faststream.kafka import KafkaBroker as NativeKafkaBroker

from fastsprout.events.event import Event, Eventable

from .transport_broker import EventMessage, TransportBroker, event_route

__all__ = ["KafkaBroker"]


class KafkaBroker(TransportBroker):
    def __init__(
        self,
        native: NativeKafkaBroker,
        *,
        route: Callable[[type[Eventable]], str] = event_route,
        group_id: str | None = "fastsprout",
        subscription: Callable[
            [type[Event], Callable[[EventMessage], Awaitable[None]]],
            Callable[[], Awaitable[None]],
        ]
        | None = None,
    ) -> None:
        super().__init__()
        self.native = native
        self.route = route
        self.group_id = group_id
        self.subscription = subscription

    async def connect(self) -> None:
        await self.native.connect()

    def register(
        self,
        event_type: type[Event],
        handler: Callable[[EventMessage], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]:
        if self.subscription is not None:
            return self.subscription(event_type, handler)
        subscriber = self.native.subscriber(
            self.route(event_type),
            group_id=self.group_id,
            auto_offset_reset="earliest",
        )
        subscriber(handler)
        return subscriber.start

    async def send(
        self, message: EventMessage, event_type: type[Eventable]
    ) -> None:
        await self.native.publish(
            message,
            topic=self.route(event_type),
            key=message.event_id.bytes,
        )

    async def stop(self) -> None:
        try:
            await super().stop()
        finally:
            await self.native.stop()
