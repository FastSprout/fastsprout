from collections.abc import Awaitable, Callable

from faststream.nats import NatsBroker as NativeNatsBroker

from fastsprout.events.event import Event, Eventable

from .transport_broker import EventMessage, TransportBroker, event_route

__all__ = ["NATSBroker"]


class NATSBroker(TransportBroker):
    def __init__(
        self,
        native: NativeNatsBroker,
        *,
        route: Callable[[type[Eventable]], str] = event_route,
        subscription: Callable[
            [type[Event], Callable[[EventMessage], Awaitable[None]]],
            Callable[[], Awaitable[None]],
        ]
        | None = None,
    ) -> None:
        super().__init__()
        self.native = native
        self.route = route
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
        subscriber = self.native.subscriber(self.route(event_type))
        subscriber(handler)
        return subscriber.start

    async def send(
        self, message: EventMessage, event_type: type[Eventable]
    ) -> None:
        await self.native.publish(message, subject=self.route(event_type))

    async def stop(self) -> None:
        try:
            await super().stop()
        finally:
            await self.native.stop()
